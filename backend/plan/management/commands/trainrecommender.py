import codecs
import csv
import math
import os
import pickle
from typing import Dict, Iterable, List, Tuple

import numpy as np
from django.core.cache import cache
from django.core.management.base import BaseCommand
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from courses.management.commands.recommendation_utils.utils import sections_to_courses, sem_to_key
from courses.models import Course
from PennCourses.settings.production import S3_client, S3_resource
from plan.models import Schedule


def lookup_course(course):
    try:
        return Course.objects.filter(full_code=course).latest("semester")
    except Course.DoesNotExist:
        return None


def courses_data_from_db():
    """
    Fetches data from the courses db and yields tuples of the form person_id, course, semester
    """
    for schedule in Schedule.objects.all():
        for course in sections_to_courses(schedule.sections.all()):
            person_id = schedule.person.pk
            yield person_id, course, schedule.semester


def courses_data_from_csv(course_data_path):
    with open(course_data_path) as course_data_file:
        data_reader = csv.reader(course_data_file)
        for row in data_reader:
            yield tuple(row)


def courses_data_from_s3():
    for row in csv.reader(
        codecs.getreader("utf-8")(
            S3_client.get_object(Bucket="penn.courses", Key="course_data.csv")["Body"]
        )
    ):
        yield tuple(row)


def get_description(course):
    course_obj = lookup_course(course)
    if course_obj is None or not course_obj.description:
        return ""
    return course_obj.description


def vectorize_courses_by_description(courses):
    descriptions = [get_description(course) for course in courses]
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(descriptions)
    dim_reducer = TruncatedSVD(n_components=500)
    vectors = dim_reducer.fit_transform(vectors)
    # divide the vectors by their norms
    return normalize(vectors)


def group_courses(courses_data: Iterable[Tuple[int, str, str]]):
    """
    :param courses_data: An iterable of person id, course string, semester string
    :return:
    """
    # The dict below stores a person_id in association with a dict that associates
    # a semester with a multiset of the courses taken during that semester. The reason this is a
    # multiset is to take into account users with multiple mock schedules.
    # This is an intermediate data form that is used to construct the two dicts returned.
    courses_by_semester_by_user: Dict[int, Dict[str, Dict[str, int]]] = {}
    for person_id, course, semester in courses_data:
        # maps a course to a list of semesters
        if person_id not in courses_by_semester_by_user:
            user_dict = {}
            courses_by_semester_by_user[person_id] = user_dict
        else:
            user_dict = courses_by_semester_by_user[person_id]

        if semester not in user_dict:
            semester_courses_multiset = {}
            user_dict[semester] = semester_courses_multiset
        else:
            semester_courses_multiset = user_dict[semester]

        if course in semester_courses_multiset:
            semester_courses_multiset[course] += 1
        else:
            semester_courses_multiset[course] = 1

    return courses_by_semester_by_user


def vectorize_by_copresence(
    courses_by_semester_by_user, as_past_class=False
) -> Dict[str, np.ndarray]:
    """
    Vectorizes courses by whether they're in the user's schedule at the same time,
    as well as the number of times they come after other courses.
    :param courses_by_semester_by_user: Grouped courses data returned by group_courses
    :return:
    """
    courses_set = set()
    for _, courses_by_semester in courses_by_semester_by_user.items():
        for _, course_multiset in courses_by_semester.items():
            for course, _ in course_multiset.items():
                courses_set.add(course)
    courses_list = list(courses_set)
    course_to_index = {course: i for i, course in enumerate(courses_list)}

    copresence_vectors_by_course = {course: np.zeros(len(courses_list)) for course in courses_list}
    order_vectors_by_course = {course: np.zeros(len(courses_list)) for course in courses_list}

    for user, courses_by_semester in courses_by_semester_by_user.items():
        for sem, course_multiset in courses_by_semester.items():
            for course_a, frequency_a in course_multiset.items():
                index_a = course_to_index[course_a]
                relevant_vector_a = copresence_vectors_by_course[course_a]
                # A past class does not occur with classes in the same semester
                if not as_past_class:
                    for course_b, frequency_b in course_multiset.items():
                        co_frequency = min(frequency_a, frequency_b)
                        index_b = course_to_index[course_b]
                        relevant_vector_a[index_b] += co_frequency
                # make sure that every course appears with itself
                relevant_vector_a[index_a] += frequency_a
        ordered_sems = sorted(courses_by_semester, key=sem_to_key)
        for i, sem in enumerate(ordered_sems):
            courses_first_sem = courses_by_semester[sem]
            # if this class is being encoded as a past class, it happens after itself
            start_sem_index = i if as_past_class else i + 1
            for later_sem in ordered_sems[start_sem_index:]:
                courses_later_sem = courses_by_semester[later_sem]
                for course_later, freq1 in courses_later_sem.items():
                    add_to_copres = as_past_class and later_sem != ordered_sems[start_sem_index]
                    for course_earlier, freq2 in courses_first_sem.items():
                        earlier_index = course_to_index[course_earlier]
                        cofreq = min(freq1, freq2)
                        order_vectors_by_course[course_later][earlier_index] += cofreq
                        if add_to_copres:
                            later_index = course_to_index[course_later]
                            copresence_vectors_by_course[course_earlier][later_index] += cofreq

    concatenated = {
        key: order_vectors_by_course[key] + copresence_vectors_by_course[key]
        for key in order_vectors_by_course
    }

    return concatenated


def vectorize_courses_by_schedule_presence(courses_by_user: List[Dict[str, int]]):
    """
    @:param courses_by_user: A list of dicts in which each dict maps a course id to
    the number of times a user has it in their schedules.
    :return: A dict mapping course ids to a vector wherein each component
    contains how many times the corresponding user
    has that course in their schedules.
    """
    num_users = len(courses_by_user)
    course_vectors_dict = {}
    for user_index, user_courses in enumerate(courses_by_user):
        for course, frequency in user_courses.items():
            relevant_vector: np.ndarray
            if course not in course_vectors_dict:
                relevant_vector = np.zeros(num_users)
                course_vectors_dict[course] = relevant_vector
            else:
                relevant_vector = course_vectors_dict[course]
            relevant_vector[user_index] = frequency

    courses, vectors = zip(*course_vectors_dict.items())
    # reduce dimensionality to the log of the number of users
    vectors = np.array(vectors)
    dim_reducer = PCA(n_components=round(math.log2(num_users + 2)))
    dim_reduced = dim_reducer.fit_transform(vectors)
    # divide the vectors by the average norm
    scaled = normalize(dim_reduced)
    return {course: scaled for course, scaled in zip(courses, scaled)}


def get_unsequenced_courses_by_user(courses_by_semester_by_user):
    """
    Takes in grouped courses data and returns a list of multisets,
    wherein each multiset is the multiset of courses
    for a particular user
    :param courses_by_semester_by_user: Grouped courses data returned by group_courses
    :return:
    """
    unsequenced_courses_by_user = {}
    for user, courses_by_semester in courses_by_semester_by_user.items():
        combined_multiset = {}
        for semester, course_multiset in courses_by_semester.items():
            for course, frequency in course_multiset.items():
                combined_multiset[course] = frequency
        unsequenced_courses_by_user[user] = combined_multiset

    return list(unsequenced_courses_by_user.values())


def generate_course_vectors_dict(courses_data, use_descriptions=True):
    """
    Generates a dict associating courses to vectors for those courses,
    as well as courses to vector representations
    of having taken that class in the past.
    """
    courses_to_vectors_curr = {}
    courses_to_vectors_past = {}
    grouped_courses = group_courses(courses_data)
    copresence_vectors_by_course = vectorize_by_copresence(grouped_courses)
    copresence_vectors_by_course_past = vectorize_by_copresence(grouped_courses, as_past_class=True)
    courses_by_user = get_unsequenced_courses_by_user(grouped_courses)

    courses, courses_vectorized_by_schedule_presence = zip(
        *vectorize_courses_by_schedule_presence(courses_by_user).items()
    )
    courses_vectorized_by_description = vectorize_courses_by_description(courses)
    copresence_vectors = [copresence_vectors_by_course[course] for course in courses]
    copresence_vectors_past = [copresence_vectors_by_course_past[course] for course in courses]
    copresence_vectors = normalize(copresence_vectors)
    copresence_vectors_past = normalize(copresence_vectors_past)
    dim_reduce = TruncatedSVD(n_components=round(30 * math.log2(len(courses))))
    copresence_vectors = dim_reduce.fit_transform(copresence_vectors)
    dim_reduce = TruncatedSVD(n_components=round(30 * math.log2(len(courses))))
    copresence_vectors_past = dim_reduce.fit_transform(copresence_vectors_past)
    for (
        course,
        schedule_vector,
        description_vector,
        copresence_vector,
        copresence_vector_past,
    ) in zip(
        courses,
        courses_vectorized_by_schedule_presence,
        courses_vectorized_by_description,
        copresence_vectors,
        copresence_vectors_past,
    ):
        if use_descriptions:
            if np.linalg.norm(description_vector) == 0:
                continue
            total_vector_curr = np.concatenate(
                [schedule_vector, description_vector, copresence_vector * 2]
            )
            total_vector_past = np.concatenate(
                [schedule_vector, description_vector, copresence_vector_past * 2]
            )
        else:
            total_vector_curr = np.concatenate([schedule_vector, copresence_vector * 2])
            total_vector_past = np.concatenate([schedule_vector, copresence_vector_past * 2])
        courses_to_vectors_curr[course] = total_vector_curr / np.linalg.norm(total_vector_curr)
        courses_to_vectors_past[course] = total_vector_past / np.linalg.norm(total_vector_past)
    return courses_to_vectors_curr, courses_to_vectors_past


def normalize_class_name(class_name):
    """
    Take in a class name and return the standard name for that class
    """
    course_obj: Course = lookup_course(class_name)
    if course_obj is None:
        return class_name
    class_name = course_obj.primary_listing.full_code
    return class_name


def cosine_similarity(vec_a, vec_b):
    np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))


def generate_course_clusters(courses_data, n_per_cluster=100):
    """
    Clusters courses and also returns a vector representation of each class
    (one for having taken that class now, and another for having taken it in the past)
    """
    course_vectors_dict_curr, course_vectors_dict_past = generate_course_vectors_dict(courses_data)
    _courses, _course_vectors = zip(*course_vectors_dict_curr.items())
    courses, course_vectors = list(_courses), np.array(list(_course_vectors))
    num_clusters = round(len(courses) / n_per_cluster)
    model = KMeans(n_clusters=num_clusters)
    raw_cluster_result = model.fit_predict(course_vectors)
    clusters = [[] for _ in range(num_clusters)]
    for course_index, cluster_index in enumerate(raw_cluster_result):
        clusters[cluster_index].append(courses[course_index])

    cluster_centroids = [
        sum(course_vectors_dict_curr[course] for course in cluster) / len(cluster)
        for cluster in clusters
    ]
    return cluster_centroids, clusters, course_vectors_dict_curr, course_vectors_dict_past


def train_recommender(
    course_data_path=None,
    train_from_s3=False,
    output_path=None,
    upload_to_s3=False,
    n_per_cluster=100,
    verbose=False,
):
    # input validation
    if train_from_s3:
        assert (
            course_data_path is None
        ), "If you are training on data from S3, there's no need to supply a local data path"
    if course_data_path is not None:
        assert course_data_path.endswith(".csv"), "Local data path must be .csv"
    if output_path is None:
        assert upload_to_s3, "You must either specify an output path, or upload to S3"
    if upload_to_s3:
        assert output_path is None, (
            "If you are uploading the trained model to S3, there's no need to specify an "
            "output path."
        )
    else:
        assert output_path is not None, "You must either specify an output path, or upload to S3"
        assert (
            output_path.endswith(".pkl") or output_path == os.devnull
        ), "Output file must have a .pkl extension"

    if not upload_to_s3 and not output_path.endswith("course-cluster-data.pkl") and verbose:
        print(
            "Warning: The name of the course recommendation model used in prod (stored in S3)"
            "must be course-cluster-data.pkl."
        )
    if verbose:
        print("Training...")

    if train_from_s3:
        courses_data = courses_data_from_s3()
    else:
        courses_data = (
            courses_data_from_csv(course_data_path)
            if course_data_path is not None
            else courses_data_from_db()
        )
    course_clusters = generate_course_clusters(courses_data, n_per_cluster)

    if upload_to_s3:
        S3_resource.Object("penn.courses", "course-cluster-data.pkl").put(
            Body=pickle.dumps(course_clusters)
        )
        cache.set("course-cluster-data", course_clusters, timeout=90000)
    else:
        pickle.dump(
            course_clusters, open(output_path, "wb"),
        )

    if verbose:
        print("Done!")

    return course_clusters


class Command(BaseCommand):
    help = (
        "Use this script to train a PCP course recommendation model on given training data "
        "(specified via a local path), and output the trained model (as a .pkl file) to a "
        "specified local filepath.\n"
        "If you overwrite the course-cluster-data.pkl object in the penn.courses S3 bucket, "
        "the course recommendation model actually used in prod will be updated within 25 hours, "
        "or when , whichever comes first."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--course_data_path",
            type=str,
            default=None,
            help=(
                "The local path to the training data csv. If this argument is omitted, the model "
                "will be trained on Schedule data from the db (this only makes sense in prod).\n"
                "The csv pointed to by this path should have 3 columns:\n"
                "person_id, course, semester"
                "\nThe person_id column should contain a user hash, the course column should "
                "contain the course code (in the format DEPT-XXX, e.g. CIS-120), and "
                "the semester column should contain  the semester in which the course was taken "
                "by that user."
            ),
        )
        parser.add_argument(
            "--train_from_s3",
            default=False,
            action="store_true",
            help=(
                "Enable this argument to train this model using data stored in S3. If this "
                "argument is flagged, the course_data_path argument must be omitted."
            ),
        )
        parser.add_argument(
            "--output_path",
            default=None,
            type=str,
            help="The local path where the model pkl should be saved.",
        )
        parser.add_argument(
            "--upload_to_s3",
            default=False,
            action="store_true",
            help=(
                "Enable this argument to upload this model to S3, replacing the "
                "course-cluster-data.pkl key in the penn.courses bucket. "
                "If this argument is flagged, the output_path argument must be omitted."
            ),
        )
        parser.add_argument(
            "--n_per_cluster",
            type=int,
            default=100,
            help="The number of courses to include in each cluster (a hyperparameter). "
            "Defaults to 100.",
        )

    def handle(self, *args, **kwargs):
        course_data_path = kwargs["course_data_path"]
        train_from_s3 = kwargs["train_from_s3"]
        output_path = kwargs["output_path"]
        upload_to_s3 = kwargs["upload_to_s3"]
        n_per_cluster = kwargs["n_per_cluster"]

        train_recommender(
            course_data_path=course_data_path,
            train_from_s3=train_from_s3,
            output_path=output_path,
            upload_to_s3=upload_to_s3,
            n_per_cluster=n_per_cluster,
            verbose=True,
        )