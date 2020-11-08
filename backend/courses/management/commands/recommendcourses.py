import heapq
import pickle
from typing import Set, Optional

import numpy as np
from accounts.middleware import User
from django.core.management.base import BaseCommand

from courses.management.commands.recommendation_utils.utils import sections_to_courses
from plan.models import Schedule


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


def retrieve_course_clusters():
    return pickle.load(open("./course-cluster-data.pkl", "rb"))


class Command(BaseCommand):
    help = 'Recommend courses for a user.'

    def add_arguments(self, parser):
        parser.add_argument('--user', nargs='?', type=str)
        parser.add_argument('--courses', nargs='?', type=str)

    def handle(self, *args, **kwargs):

        cluster_centroids, clusters, course_vectors_dict = retrieve_course_clusters()
        if "user" in kwargs and kwargs["user"] is not None:
            user_vector, user_courses = vectorize_user(kwargs["user"], course_vectors_dict)
        else:
            user_vector, user_courses = vectorize_user_by_courses(kwargs["courses"].split(","), course_vectors_dict)

        print(recommend_courses(course_vectors_dict, cluster_centroids, clusters, user_vector, user_courses))
