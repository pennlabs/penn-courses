import json
import logging
import os

from django.core.management.base import BaseCommand
from tqdm import tqdm

from courses.models import Course, Department, Instructor
from review.views import (
    manual_course_plots,
    manual_course_reviews,
    manual_department_reviews,
    manual_instructor_for_course_reviews,
    manual_instructor_reviews,
)


def save_object(id, type, data):
    """
    Common save object method to act as interface for any precomputation
    – either as S3 objects or storing directly in PostgreSQL.
    """
    with open(os.path.expanduser(f"~/Desktop/pcr_test_data/{type}-{id}.json"), "w") as f:
        json.dump(data, f, indent=4)


def precompute_instructors(verbose=False, sample_size=0):
    """
    Precompute all JSON data needed for PCR instructor views.
    """
    if verbose:
        print("Precomputing instructor view data.")

    count = 0
    for instructor in tqdm(Instructor.objects.all()):
        if count == sample_size:
            return
        
        instructor_id = instructor.id
        reviews = manual_instructor_reviews(instructor_id)

        if not reviews:
            continue

        review_json = {"summary": reviews, "sections": {}}
        for course_code in reviews["courses"]:
            section_reviews = manual_instructor_for_course_reviews(
                semester=None, course_code=course_code, instructor_id=instructor_id
            )
            if section_reviews:
                review_json["sections"][course_code] = section_reviews

        save_object(instructor_id, "INSTR", review_json)
        count += 1


def precompute_departments(verbose=False, sample_size=0):
    """
    Precompute all JSON data needed for PCR department views.
    """
    if verbose:
        print("Precomputing department view data.")

    count = 0
    for department in tqdm(Department.objects.all()):
        if count == sample_size:
            return

        department_code = department.code
        reviews = manual_department_reviews(department_code)
        if reviews:
            save_object(department_code, "DEPT", reviews)
            count += 1


def precompute_courses(verbose=False, semester=None, sample_size=0):
    """
    Precompute all JSON data needed for PCR courses views.
    """
    if verbose:
        print("Precomputing course view data.")

    count = 0
    for course in tqdm(Course.objects.all()):
        if count == sample_size:
            return
        
        course_code = course.full_code

        # Fetch Course Summary
        reviews = manual_course_reviews(course_code, None)
        if not reviews:
            continue
        review_json = {"summary": reviews, "sections": {}}

        # Fetch Section Data
        for instructor_id in reviews["instructors"]:
            instructor_reviews = manual_instructor_for_course_reviews(
                semester=None, course_code=course_code, instructor_id=instructor_id
            )
            if instructor_reviews:
                review_json["sections"][instructor_id] = instructor_reviews

        # Fetch Course Plots
        plots = manual_course_plots(semester, None, course_code)
        review_json["plots"] = plots
        if "current_add_drop_period" in review_json["plots"]:
            review_json["plots"]["current_add_drop_period"]["start"] = str(
                review_json["plots"]["current_add_drop_period"]["start"]
            )
            review_json["plots"]["current_add_drop_period"]["end"] = str(
                review_json["plots"]["current_add_drop_period"]["end"]
            )

        save_object(course_code, "COURSE", review_json)
        count += 1


class Command(BaseCommand):
    help = "Precompute all data needed for Penn Course Review and store in S3"

    def add_arguments(self, parser):
        parser.add_argument("--semester", default=None, type=str)

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        sample_size = 5

        test_path = os.path.expanduser("~/Desktop/pcr_test_data/")
        if not os.path.exists(test_path):
            os.makedirs(test_path)

        precompute_instructors(verbose=True, sample_size=sample_size)
        precompute_departments(verbose=True, sample_size=sample_size)
        precompute_courses(verbose=True, semester=kwargs["semester"], sample_size=sample_size)
