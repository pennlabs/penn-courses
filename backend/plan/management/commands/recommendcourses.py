import heapq
import pickle
from typing import Optional, Set

import numpy as np
from accounts.middleware import User
from django.core.cache import cache
from django.core.management.base import BaseCommand

from courses.models import Course
from courses.util import get_current_semester
from PennCourses.settings.production import S3_client
from plan.management.commands.utils import sections_to_courses, sem_to_key
from plan.models import Schedule


def vectorize_user_by_courses(
    curr_courses, past_courses, curr_course_vectors_dict, past_course_vectors_dict
):
    n = len(next(iter(curr_course_vectors_dict.values())))

    # Input validation
    all_courses = set(curr_courses) | set(past_courses)
    if len(all_courses) != len(curr_courses) + len(past_courses):
        raise ValueError(
            "Repeated courses given in curr_courses and/or past_courses. "
            f"curr_courses: {str(curr_courses)}. past_courses: {str(past_courses)}"
        )
    invalid_curr_courses = set(curr_courses) - {
        c.full_code
        for c in Course.objects.filter(semester=get_current_semester(), full_code__in=curr_courses)
    }
    if len(invalid_curr_courses) > 0:
        raise ValueError(
            "The following courses in curr_courses are invalid or not offered this semester:"
            f"{str(invalid_curr_courses)}"
        )
    invalid_past_courses = set(past_courses) - {
        c.full_code for c in Course.objects.filter(full_code__in=past_courses)
    }
    if len(invalid_past_courses) > 0:
        raise ValueError(
            "The following courses in past_courses are invalid:" f"{str(invalid_past_courses)}"
        )

    # Eliminate courses not in the model
    curr_courses = [c for c in curr_courses if c in curr_course_vectors_dict]
    past_courses = [c for c in past_courses if c in past_course_vectors_dict]
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
    norm = np.linalg.norm(vector)
    vector = vector / norm if norm > 0 else vector
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
    rec_course_to_score = {course: score for course, score in recs}
    recs = [
        (c.full_code, rec_course_to_score[c.full_code])
        for c in Course.objects.filter(
            semester=get_current_semester(), full_code__in=list(rec_course_to_score.keys())
        )
    ]  # only recommend currently offered courses
    if n_recommendations > len(recs):
        n_recommendations = len(recs)

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
    cached_data = cache.get("course-cluster-data", None)
    if cached_data is not None:
        return cached_data
    # Need to redownload
    course_cluster_data = pickle.loads(
        S3_client.get_object(Bucket="penn.courses", Key="course-cluster-data.pkl")["Body"].read()
    )
    cache.set("course-cluster-data", course_cluster_data, timeout=90000)
    return course_cluster_data


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
