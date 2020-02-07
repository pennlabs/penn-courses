import math
from collections import defaultdict
from typing import Set, List, Dict

import numpy as np
from accounts.middleware import User
from django.core.management.base import BaseCommand
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from courses.models import Course
from plan.models import Schedule


def sections_to_courses(sections) -> Set[str]:
    """
    Encodes a list section objects as a set of the base course code (e.g., CIS-140)
    :param sections: A section object list
    :return: A string set
    """
    return {str(section.course).split(" ")[0] for section in sections}


def vectorize_user(user, course_vectors_dict):
    """
    Aggregates a vector over all the courses in the user's schedule
    :param user:
    :param course_vectors:
    :return:
    """
    user_pk = User.objects.filter(username=user)[0].pk
    return sum(
        course_vectors_dict[course] for schedule in Schedule.objects.filter(person=user_pk)
        for course in sections_to_courses(schedule.sections.all()))


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
    norm_avg = sum(np.linalg.norm(vector) for vector in dim_reduced) / len(dim_reduced)
    scaled = np.array([vector / norm_avg for vector in dim_reduced])
    return {course: scaled for course, scaled in zip(courses, scaled)}


def vectorize_courses_by_description(courses):
    descriptions = [Course.objects.filter(full_code=course)[0].description for course in courses]
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(descriptions)
    dim_reducer = TruncatedSVD(n_components=200)
    vectors = dim_reducer.fit_transform(vectors)
    # divide the vectors by the average norm
    norm_avg = sum(np.linalg.norm(vector) for vector in vectors) / len(vectors)
    scaled = np.array([vector / norm_avg for vector in vectors])
    return scaled


def generate_course_vectors_dict():
    courses_to_vectors = {}
    courses, courses_vectorized_by_schedule_presence = zip(
        *vectorize_courses_by_schedule_presence(generate_courses_by_user()).items())
    courses_vectorized_by_description = vectorize_courses_by_description(courses)
    for course, schedule_vector, description_vector in zip(courses, courses_vectorized_by_schedule_presence,
                                                           courses_vectorized_by_description):
        total_vector = np.concatenate([schedule_vector, description_vector])
        courses_to_vectors[course] = total_vector
    return courses_to_vectors


def generate_course_clusters():
    course_vectors_dict = generate_course_vectors_dict()
    _courses, _course_vectors = zip(*course_vectors_dict.items())
    courses, course_vectors = list(_courses), np.array(list(_course_vectors))
    num_clusters = 3
    model = AgglomerativeClustering(n_clusters=num_clusters, linkage="average", affinity="cosine")
    raw_cluster_result = model.fit_predict(course_vectors)
    clusters = [[] for _ in range(num_clusters)]
    for course_index, cluster_index in enumerate(raw_cluster_result):
        clusters[cluster_index].append(courses[course_index])

    cluster_centroids = [sum(course_vectors_dict[course] for course in cluster) / len(cluster) for cluster in
                         clusters]
    return cluster_centroids, clusters, course_vectors_dict


class Command(BaseCommand):
    help = 'Recommend courses for a user.'

    def add_arguments(self, parser):
        parser.add_argument('--user', nargs='?', type=str)

    def handle(self, *args, **kwargs):
        if "user" not in kwargs or kwargs["user"] is None:
            raise Exception("User not defined")

        cluster_centroids, clusters, course_vectors_dict = generate_course_clusters()
        user_vector = vectorize_user(kwargs["user"], course_vectors_dict)

        max_similarity = 0
        best_cluster_index = -1
        for cluster_index, centroid in enumerate(cluster_centroids):
            similarity = np.dot(centroid, user_vector) / (np.linalg.norm(centroid) * np.linalg.norm(user_vector))
            if similarity > max_similarity:
                max_similarity = similarity
                best_cluster_index = cluster_index

        print(clusters[best_cluster_index])
