import heapq
import pickle
from typing import Optional, Set

import numpy as np
from accounts.middleware import User
from django.core.management.base import BaseCommand

from courses.management.commands.recommendation_utils.utils import sections_to_courses, sem_to_key
from courses.util import get_current_semester
from plan.models import Schedule


def vectorize_user_by_courses(
    curr_courses, past_courses, curr_course_vectors_dict, past_course_vectors_dict
):
    n = len(next(iter(curr_course_vectors_dict.values())))
    curr_courses_vector = (
        np.zeros(n)
        if len(curr_courses) == 0
        else sum(curr_course_vectors_dict[course] for course in curr_courses)
    )
    past_courses_vector = (
        np.zeros(n)
        if len(past_courses) == 0
        else sum(past_course_vectors_dict[course] for course in past_courses)
    )
    vector = curr_courses_vector + past_courses_vector
    vector = vector / np.linalg.norm(vector)
    all_courses = set(curr_courses) | set(past_courses)
    return vector, all_courses


def vectorize_user(user, curr_course_vectors_dict, past_course_vectors_dict):
    """
    Aggregates a vector over all the courses in the user's schedule
    :param user:
    :param course_vectors:
    :return:
    """

    user_pk = User.objects.filter(username=user)[0].pk
    curr_semester = get_current_semester()
    curr_sem_key = sem_to_key(curr_semester)
    curr_courses = [
        course
        for schedule in Schedule.objects.filter(person=user_pk)
        for course in sections_to_courses(schedule.sections.all())
        if schedule.semester == curr_semester
    ]
    past_courses = [
        course
        for schedule in Schedule.objects.filter(person=user_pk)
        if sem_to_key(schedule.semester) < curr_sem_key
        for course in sections_to_courses(schedule.sections.all())
    ]
    return vectorize_user_by_courses(
        curr_courses, past_courses, curr_course_vectors_dict, past_course_vectors_dict
    )


def best_recommendations(
    cluster,
    curr_course_vectors_dict,
    user_vector,
    exclude: Optional[Set[str]] = None,
    n_recommendations=5,
):
    recs = []
    for course in cluster:
        if exclude is not None and course in exclude:
            continue
        course_vector = curr_course_vectors_dict[course]
        similarity = np.dot(course_vector, user_vector) / (
            np.linalg.norm(course_vector) * np.linalg.norm(user_vector)
        )
        recs.append((course, similarity))
    return [course for course, _ in heapq.nlargest(n_recommendations, recs, lambda x: x[1])]


def recommend_courses(
    curr_course_vectors_dict,
    cluster_centroids,
    clusters,
    user_vector,
    user_courses,
    n_recommendations=5,
):
    min_distance = -1
    best_cluster_index = -1
    for cluster_index, centroid in enumerate(cluster_centroids):
        distance = np.linalg.norm(centroid - user_vector)
        if best_cluster_index == -1 or distance < min_distance:
            min_distance = distance
            best_cluster_index = cluster_index

    return best_recommendations(
        clusters[best_cluster_index],
        curr_course_vectors_dict,
        user_vector,
        exclude=user_courses,
        n_recommendations=n_recommendations,
    )


def retrieve_course_clusters():
    return pickle.load(open("./course-cluster-data.pkl", "rb"))


def clean_course_input(course_input):
    return [course for course in course_input if len(course) > 0]


class Command(BaseCommand):
    help = "Recommend courses for a user."

    def add_arguments(self, parser):
        parser.add_argument("--user", nargs="?", type=str)
        parser.add_argument("--curr_courses", nargs="?", type=str)
        parser.add_argument("--past_courses", nargs="?", type=str)

    def handle(self, *args, **kwargs):

        (
            cluster_centroids,
            clusters,
            curr_course_vectors_dict,
            past_course_vectors_dict,
        ) = retrieve_course_clusters()
        if "user" in kwargs and kwargs["user"] is not None:
            user_vector, user_courses = vectorize_user(
                kwargs["user"], curr_course_vectors_dict, past_course_vectors_dict
            )
        else:
            user_vector, user_courses = vectorize_user_by_courses(
                clean_course_input(kwargs["curr_courses"].split(",")),
                clean_course_input(kwargs["past_courses"].split(",")),
                curr_course_vectors_dict,
                past_course_vectors_dict,
            )

        print(
            recommend_courses(
                curr_course_vectors_dict, cluster_centroids, clusters, user_vector, user_courses
            )
        )
