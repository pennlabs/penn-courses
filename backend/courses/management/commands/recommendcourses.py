import heapq
import itertools
import math
from typing import Set, List, Dict, Optional, Tuple, Iterable, Generator

import numpy as np
from accounts.middleware import User
from django.core.management.base import BaseCommand
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from courses.models import Course
from plan.models import Schedule


def cache_result(function):
    memo = {}

    def inner(*args, **kwargs):
        if len(memo) > 0:
            return memo["val"]
        result = function(*args, **kwargs)
        memo["val"] = result
        return result

    return inner


def lookup_course(course):
    try:
        return Course.objects.filter(full_code=course)[0]
    except Exception:
        return None


def normalize_class_name(class_name):
    course_obj: Course = lookup_course(class_name)
    if course_obj is None:
        return class_name
    class_name = str(course_obj.primary_listing)
    if " " in class_name:
        class_name = class_name.split(" ")[0]
    return class_name


def sections_to_courses(sections) -> Set[str]:
    """
    Encodes a list of section objects as a set of the base course code (e.g., CIS-140)
    :param sections: A section object list
    :return: A string set
    """
    return {str(section.course).split(" ")[0] for section in sections}


def cosine_similarity(vec_a, vec_b):
    np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))


def vectorize_user_by_courses(courses, course_vectors_dict):
    vector = sum(course_vectors_dict[course] for course in courses)
    vector = vector / np.linalg.norm(vector)
    return vector, set(courses)


def vectorize_user(user, course_vectors_dict):
    """
    Aggregates a vector over all the courses in the user's schedule
    :param user:
    :param course_vectors:
    :return:
    """
    user_pk = User.objects.filter(username=user)[0].pk
    courses = [course for schedule in Schedule.objects.filter(person=user_pk)
               for course in sections_to_courses(schedule.sections.all())]
    return vectorize_user_by_courses(courses, course_vectors_dict)


def courses_data_from_db():
    """
    Fetches data from the courses db and yields tuples of the form person_id, course, semester
    """
    for schedule in Schedule.objects.all():
        for course in sections_to_courses(schedule.sections.all()):
            person_id = schedule.person.pk
            yield (person_id, course, schedule.semester)


def courses_data_from_csv():
    for line in open("./course_data.csv", "r"):
        yield tuple(line.split(","))


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


def get_unsequenced_courses_by_user(courses_by_semester_by_user):
    """
    Takes in grouped courses data and returns a list of multisets, wherein each multiset is the multiset of courses
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


def vectorize_by_copresence(courses_by_semester_by_user) -> Dict[str, np.ndarray]:
    """
    Vectorizes courses by whether they're in the user's schedule at the same time
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

    for user, courses_by_semester in courses_by_semester_by_user.items():
        for _, course_multiset in courses_by_semester.items():
            for course_a, frequency_a in course_multiset.items():
                for course_b, frequency_b in course_multiset.items():
                    co_frequency = min(frequency_a, frequency_b)
                    relevant_vector_a = copresence_vectors_by_course[course_a]
                    relevant_vector_b = copresence_vectors_by_course[course_b]
                    index_a = course_to_index[course_a]
                    index_b = course_to_index[course_b]
                    relevant_vector_a[index_b] += co_frequency
                    relevant_vector_b[index_a] += co_frequency
                    # make sure that every course appears with itself
                    relevant_vector_a[index_a] += frequency_a
                    relevant_vector_a[index_b] += frequency_b
    return copresence_vectors_by_course


def vectorize_courses_by_schedule_presence(courses_by_user: List[Dict[str, int]]):
    """
    @:param courses_by_user: A list of dicts in which each dict maps a course id to the number of times a user has it
    in their schedules.
    :return: A dict mapping course ids to a vector wherein each component contains how many times the corresponding user
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


def get_description(course):
    course_obj = lookup_course(course)
    if course_obj is None:
        return ""
    return course_obj.description


def find_prereqs(course_lists):
    """
    Determines lists of prereqs based on which courses are taken after another course the vast majority of the time they're
    taken
    :param course_lists:
    :return:
    """
    prereqs = {}
    for course_sequence in course_lists:
        pass


def vectorize_courses_by_description(courses):
    descriptions = [get_description(course) for course in courses]
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(descriptions)
    dim_reducer = TruncatedSVD(n_components=500)
    vectors = dim_reducer.fit_transform(vectors)
    # divide the vectors by their norms
    return normalize(vectors)


def generate_course_vectors_dict(from_csv=True, use_descriptions=True):
    courses_to_vectors = {}
    courses_data = courses_data_from_csv() if from_csv else courses_data_from_db()
    grouped_courses = group_courses(courses_data)
    copresence_vectors_by_course = vectorize_by_copresence(grouped_courses)
    courses_by_user = get_unsequenced_courses_by_user(grouped_courses)

    courses, courses_vectorized_by_schedule_presence = zip(
        *vectorize_courses_by_schedule_presence(courses_by_user).items())
    courses_vectorized_by_description = vectorize_courses_by_description(courses)
    copresence_vectors = [copresence_vectors_by_course[course] for course in courses]
    copresence_vectors = normalize(copresence_vectors)
    dim_reduce = TruncatedSVD(n_components=round(10 * math.log2(len(courses))))
    copresence_vectors = dim_reduce.fit_transform(copresence_vectors)
    for course, schedule_vector, description_vector, copresence_vector in zip(courses,
                                                                              courses_vectorized_by_schedule_presence,
                                                                              courses_vectorized_by_description,
                                                                              copresence_vectors):
        if use_descriptions:
            if np.linalg.norm(description_vector) == 0:
                continue
            total_vector = np.concatenate([schedule_vector, description_vector, copresence_vector])
        else:
            total_vector = np.concatenate([schedule_vector, copresence_vector])
        courses_to_vectors[course] = total_vector / np.linalg.norm(total_vector)
    return courses_to_vectors


def generate_course_clusters(n_per_cluster=100):
    course_vectors_dict = generate_course_vectors_dict()
    _courses, _course_vectors = zip(*course_vectors_dict.items())
    courses, course_vectors = list(_courses), np.array(list(_course_vectors))
    num_clusters = round(len(courses) / n_per_cluster)
    model = KMeans(n_clusters=num_clusters)
    raw_cluster_result = model.fit_predict(course_vectors)
    clusters = [[] for _ in range(num_clusters)]
    for course_index, cluster_index in enumerate(raw_cluster_result):
        clusters[cluster_index].append(courses[course_index])

    cluster_centroids = [sum(course_vectors_dict[course] for course in cluster) / len(cluster) for cluster in
                         clusters]
    return cluster_centroids, clusters, course_vectors_dict


def best_recommendations(cluster, course_vectors_dict, user_vector, exclude: Optional[Set[str]] = None,
                         n_recommendations=5):
    recs = []
    for course in cluster:
        if exclude is not None and course in exclude:
            continue
        course_vector = course_vectors_dict[course]
        similarity = np.dot(course_vector, user_vector) / (np.linalg.norm(course_vector) * np.linalg.norm(user_vector))
        recs.append((course, similarity))
    return [course for course, _ in heapq.nlargest(n_recommendations, recs, lambda x: x[1])]


def recommend_courses(course_vectors_dict, cluster_centroids, clusters, user_vector, user_courses, n_recommendations=5):
    min_distance = -1
    best_cluster_index = -1
    for cluster_index, centroid in enumerate(cluster_centroids):
        distance = np.linalg.norm(centroid - user_vector)
        if best_cluster_index == -1 or distance < min_distance:
            min_distance = distance
            best_cluster_index = cluster_index

    return best_recommendations(clusters[best_cluster_index], course_vectors_dict, user_vector, exclude=user_courses,
                                n_recommendations=n_recommendations)


class Command(BaseCommand):
    help = 'Recommend courses for a user.'

    def add_arguments(self, parser):
        parser.add_argument('--user', nargs='?', type=str)
        parser.add_argument('--courses', nargs='?', type=str)

    def handle(self, *args, **kwargs):

        cluster_centroids, clusters, course_vectors_dict = generate_course_clusters()
        if "user" in kwargs and kwargs["user"] is not None:
            user_vector, user_courses = vectorize_user(kwargs["user"], course_vectors_dict)
        else:
            user_vector, user_courses = vectorize_user_by_courses(kwargs["courses"].split(","), course_vectors_dict)

        print(recommend_courses(course_vectors_dict, cluster_centroids, clusters, user_vector, user_courses))
