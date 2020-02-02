import math
from typing import Set

import numpy as np
from accounts.middleware import User
from django.core.management.base import BaseCommand
from sklearn.cluster import AgglomerativeClustering
from sklearn.decomposition import PCA

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


def vectorize_courses_by_schedule_presence():
    """
    Return a dict mapping course ids to a vector wherein each component contains how many times the corresponding user
    has that course in their schedules.
    :return:
    """
    users = User.objects.all()
    num_users = len(users)
    id_transformer = {user.pk: i for i, user in enumerate(users)}
    course_vectors_dict = {}
    for schedule in Schedule.objects.all():
        vector_component = id_transformer[schedule.person.pk]
        for course in sections_to_courses(schedule.sections.all()):
            relevant_vector: np.ndarray
            if course not in course_vectors_dict:
                relevant_vector = np.zeros(num_users)
                course_vectors_dict[course] = relevant_vector
            else:
                relevant_vector = course_vectors_dict[course]
            relevant_vector[vector_component] += 1
    courses, vectors = zip(*course_vectors_dict.items())
    # reduce dimensionality to the log of the number of users
    vectors = np.array(vectors)
    dim_reducer = PCA(n_components=round(math.log2(num_users + 2)))
    dim_reduced = dim_reducer.fit_transform(vectors)
    # divide the vectors by the average norm
    norm_avg = sum(np.linalg.norm(vector) for vector in dim_reduced) / len(dim_reduced)
    scaled = np.array([vector / norm_avg for vector in dim_reduced])
    return {course: scaled for course, scaled in zip(courses, scaled)}


def generate_course_vectors_dict():
    return vectorize_courses_by_schedule_presence()


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
