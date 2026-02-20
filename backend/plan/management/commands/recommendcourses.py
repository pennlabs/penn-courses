import heapq
import os
import pickle
from typing import Optional, Set

import numpy as np
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management.base import BaseCommand

from courses.models import Course
from courses.util import get_current_semester, in_dev
from PennCourses.settings.base import S3_client
from plan.management.commands.trainrecommender import train_recommender
from plan.models import Schedule


# The proportion by which to up-weight current courses
# relative to past courses when computing a user vector
CURR_COURSES_BIAS = 3


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
            "The following courses in curr_courses are invalid or not offered this semester: "
            f"{str(invalid_curr_courses)}"
        )
    invalid_past_courses = set(past_courses) - {
        c.full_code for c in Course.objects.filter(full_code__in=past_courses)
    }
    if len(invalid_past_courses) > 0:
        raise ValueError(
            f"The following courses in past_courses are invalid: {str(invalid_past_courses)}"
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

    vector = curr_courses_vector * CURR_COURSES_BIAS + past_courses_vector
    norm = np.linalg.norm(vector)
    vector = vector / norm if norm > 0 else vector
    return vector, all_courses


def vectorize_user(user, curr_course_vectors_dict, past_course_vectors_dict):
    """
    Aggregates a vector over all the courses in the user's schedule
    """
    curr_semester = get_current_semester()
    curr_courses = set(
        [
            s
            for s in Schedule.objects.filter(person=user, semester=curr_semester).values_list(
                "sections__course__full_code", flat=True
            )
            if s is not None
        ]
    )
    past_courses = set(
        [
            s
            for s in Schedule.objects.filter(person=user, semester__lt=curr_semester).values_list(
                "sections__course__full_code", flat=True
            )
            if s is not None
        ]
    )
    past_courses = past_courses - curr_courses
    return vectorize_user_by_courses(
        list(curr_courses),
        list(past_courses),
        curr_course_vectors_dict,
        past_course_vectors_dict,
    )


def cosine_similarity(v1, v2):
    norm_prod = np.linalg.norm(v1) * np.linalg.norm(v2)
    return np.dot(v1, v2) / norm_prod if norm_prod > 0 else 0


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
        similarity = cosine_similarity(course_vector, user_vector)
        recs.append((course, similarity))
    rec_course_to_score = {course: score for course, score in recs}
    recs = [
        (c.full_code, rec_course_to_score[c.full_code])
        for c in Course.objects.filter(
            semester=get_current_semester(),
            full_code__in=list(rec_course_to_score.keys()),
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


dev_course_clusters = None  # a global variable used to "cache" the course clusters in dev


def retrieve_course_clusters():
    global dev_course_clusters
    if in_dev() and os.environ.get("USE_PROD_MODEL", "false") != "true":
        if dev_course_clusters is None:
            print("TRAINING DEVELOPMENT MODEL... PLEASE WAIT")
            dev_course_clusters = train_recommender(
                course_data_path=(
                    settings.BASE_DIR + "/tests/plan/course_recs_test_data/course_data_test.csv"
                ),
                preloaded_descriptions_path=(
                    settings.BASE_DIR
                    + "/tests/plan/course_recs_test_data/course_descriptions_test.csv"
                ),
                output_path=os.devnull,
            )
            print("Done training development model.")
        return dev_course_clusters
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
    help = (
        "Use this script to recommend courses. If a username is specified, the script will "
        "predict based on that user's PCP schedules. Otherwise, the script will "
        "predict based on the provided curr_courses and past_courses lists."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            default=None,
            type=str,
            help=(
                "The username of a user you would like to predict on. If this argument is "
                "omitted, you should provide the curr_courses and/or past_courses arguments."
            ),
        )
        parser.add_argument(
            "--curr_courses",
            default="",
            type=str,
            help=(
                "A comma-separated list of courses the user is currently planning to take "
                "(each course represented by its string full code, e.g. `CIS-120` for CIS-120)."
            ),
        )
        parser.add_argument(
            "--past_courses",
            default="",
            type=str,
            help=(
                "A comma-separated list of courses the user has previously taken (each course "
                "represented by its string full code, e.g. `CIS-120` for CIS-120)."
            ),
        )

    def handle(self, *args, **kwargs):
        curr_courses = kwargs["curr_courses"].split(",")
        past_courses = kwargs["past_courses"].split(",")
        username = kwargs["username"]

        (
            cluster_centroids,
            clusters,
            curr_course_vectors_dict,
            past_course_vectors_dict,
        ) = retrieve_course_clusters()
        if username is not None:
            user = get_user_model().objects.get(username=username)
            user_vector, user_courses = vectorize_user(
                user, curr_course_vectors_dict, past_course_vectors_dict
            )
        else:
            user_vector, user_courses = vectorize_user_by_courses(
                clean_course_input(curr_courses),
                clean_course_input(past_courses),
                curr_course_vectors_dict,
                past_course_vectors_dict,
            )

        print(
            recommend_courses(
                curr_course_vectors_dict,
                cluster_centroids,
                clusters,
                user_vector,
                user_courses,
            )
        )
