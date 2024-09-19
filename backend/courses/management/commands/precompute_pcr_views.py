import logging

from django.core.management.base import BaseCommand
from tqdm import tqdm

from review.views import manual_department_reviews, manual_instructor_reviews, manual_instructor_for_course_reviews, manual_course_reviews, manual_course_plots
from courses import registrar
from courses.models import Course, Section, Department, Instructor
from courses.util import get_course_and_section, get_current_semester

def save_object(id, data):
    pass

def precompute_instructors(verbose=False, semester=None):
    if verbose:
        print("Precomputing instructor view data.")
    
    for instructor in tqdm(Instructor.objects.all()):
        instructor_id = instructor.id
        reviews = manual_instructor_reviews(instructor_id)

        if not reviews:
            continue

        review_json = {"summary": reviews, "sections": {}}
        for course_code in reviews["courses"]:
            section_reviews = manual_instructor_for_course_reviews(semester, course_code, instructor_id)
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
        course_code = course.code
        
        # Fetch Course Summary
        reviews = manual_course_reviews(course_code, semester)
        if not reviews:
            continue
        review_json = {"summary": reviews, "sections": {}}

        # Fetch Section Data
        for instructor_id in reviews["instructors"]:
            instructor_reviews = manual_instructor_for_course_reviews(semester, course_code, instructor_id)
            if instructor_reviews:
                review_json["instructors"][instructor_id] = instructor_reviews

        # Fetch Course Plots
        plots = manual_course_plots(semester, None, course_code)
        review_json["plots"] = plots

        save_object(course_code, review_json)

class Command(BaseCommand):
    help = "Precompute all data needed for Penn Course Review and store in S3"

    def add_arguments(self, parser):
        parser.add_argument("--semester", default=None, type=str)

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        precompute_instructors(verbose=True, semester=kwargs["semester"])
        precompute_departments(verbose=True, semester=kwargs["semester"])
        precompute_courses(verbose=True, semester=kwargs["semester"])