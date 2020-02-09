import heapq
import math
from typing import Set, List, Dict, Optional

import numpy as np
from accounts.middleware import User
from django.core.management.base import BaseCommand
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from courses.models import Course
from plan.models import Schedule


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


def generate_courses_by_user():
    """
    :return: A list in which each item is a dict corresponding with the multiset of courses for a particular user
    """
    courses_by_user_dict = {}
    for schedule in Schedule.objects.all():
        for course in sections_to_courses(schedule.sections.all()):
            person_id = schedule.person.pk
            user_courses: Dict[str, int]
            if person_id not in courses_by_user_dict:
                user_courses = {}
                courses_by_user_dict[person_id] = user_courses
            else:
                user_courses = courses_by_user_dict[person_id]
            course = normalize_class_name(course)
            if course in user_courses:
                user_courses[course] += 1
            else:
                user_courses[course] = 1
    return list(courses_by_user_dict.values())


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


def cache_result(function):
    memo = {}

    def inner(*args, **kwargs):
        if len(memo) > 0:
            return memo["val"]
        result = function(*args, **kwargs)
        memo["val"] = result
        return result

    return inner


@cache_result
def courses_by_user_from_csv():
    courses_by_user_dict = {}
    for line in open("./course_data.csv", "r"):
        parts = line.split(",")
        uid, course = parts[0], parts[1]
        user_courses_dict: Dict[str, int]
        if uid in courses_by_user_dict:
            user_courses_dict = courses_by_user_dict[uid]
        else:
            user_courses_dict = {}
            courses_by_user_dict[uid] = user_courses_dict
        course = normalize_class_name(course)
        if course not in user_courses_dict:
            user_courses_dict[course] = 1
        else:
            user_courses_dict[course] += 1
    return list(courses_by_user_dict.values())


def generate_course_vectors_dict(from_csv=True, use_descriptions=True):
    courses_to_vectors = {}
    courses_by_user = courses_by_user_from_csv() if from_csv else generate_courses_by_user()
    courses, courses_vectorized_by_schedule_presence = zip(
        *vectorize_courses_by_schedule_presence(courses_by_user).items())
    courses_vectorized_by_description = vectorize_courses_by_description(courses)
    for course, schedule_vector, description_vector in zip(courses, courses_vectorized_by_schedule_presence,
                                                           courses_vectorized_by_description):
        if use_descriptions:
            if np.linalg.norm(description_vector) == 0:
                continue
            total_vector = np.concatenate([schedule_vector, description_vector])
        else:
            total_vector = schedule_vector
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
