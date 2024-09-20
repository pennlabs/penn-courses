import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm
import json
import os

from courses.util import get_current_semester
from review.views import manual_department_reviews, manual_instructor_reviews, manual_instructor_for_course_reviews, manual_course_reviews, manual_course_plots
from courses.models import Course, Department, Instructor

def save_object(id, data):
    """
    Common save object method to act as interface for any precomputation – either as S3 objects or storing directly in PostgreSQL.
    """
    with open(os.path.expanduser(f"~/Desktop/test_data/{id}.json"), "w") as f:
        json.dump(data, f, indent=4)

def precompute_instructors(verbose=False):
    if verbose:
        print("Precomputing instructor view data.")
    
    for instructor in tqdm(Instructor.objects.all()):
        instructor_id = instructor.id
        reviews = manual_instructor_reviews(instructor_id)

        if not reviews:
            continue

        review_json = {"summary": reviews, "sections": {}}
        for course_code in reviews["courses"]:
            section_reviews = manual_instructor_for_course_reviews(semester=None, course_code=course_code, instructor_id=instructor_id)
            if section_reviews:
                review_json["sections"][course_code] = section_reviews
        
        save_object(instructor_id, review_json)

def precompute_departments(verbose=False):
    if verbose:
        print("Precomputing department view data.")

    for department in tqdm(Department.objects.all()):
        department_code = department.code
        reviews = manual_department_reviews(department_code)
        if reviews:
            save_object(department_code, reviews)

def precompute_courses(verbose=False, semester=None):
    if verbose:
        print("Precomputing course view data.")
    
    for course in tqdm(Course.objects.all()):
        course_code = course.full_code
        
        # Fetch Course Summary
        reviews = manual_course_reviews(course_code, None)
        if not reviews:
            continue
        review_json = {"summary": reviews, "sections": {}}

        # Fetch Section Data
        for instructor_id in reviews["instructors"]:
            instructor_reviews = manual_instructor_for_course_reviews(semester=None, course_code=course_code, instructor_id=instructor_id)
            if instructor_reviews:
                review_json["sections"][instructor_id] = instructor_reviews

        # Fetch Course Plots
        plots = manual_course_plots(semester, None, course_code)
        review_json["plots"] = plots
        if "current_add_drop_period" in review_json["plots"]:
            review_json["plots"]["current_add_drop_period"]["start"] = str(review_json["plots"]["current_add_drop_period"]["start"])
            review_json["plots"]["current_add_drop_period"]["end"] = str(review_json["plots"]["current_add_drop_period"]["end"])

        save_object(course_code, review_json)

class Command(BaseCommand):
    help = "Precompute all data needed for Penn Course Review and store in S3"

    def add_arguments(self, parser):
        parser.add_argument("--semester", default=None, type=str)

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        # precompute_instructors(verbose=True)
        # precompute_departments(verbose=True)
        precompute_courses(verbose=True, semester=kwargs["semester"])