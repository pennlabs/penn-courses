from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from review.models import PrecomputedReview

@transaction.atomic
def precompute_reviews():
    count, _ = PrecomputedReview.objects.all().delete()
    print(f"Deleted {count} rows from PrecomputedReview")
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO review_precomputedreview (instructor_id, course_id, field, num_sections, average, semester)
            SELECT
                review_review.instructor_id as instructor_id,
                courses_section.course_id AS course_id,
                review_reviewbit.field AS field,
                COUNT(review_review.section_id) AS num_sections,
                AVG(review_reviewbit.average) AS average,                               
                courses_course.semester AS semester
            FROM review_reviewbit
            INNER JOIN review_review ON review_reviewbit.review_id = review_review.id                                 
            INNER JOIN courses_section ON review_review.section_id = courses_section.id
            INNER JOIN courses_course ON courses_section.course_id = courses_course.id
            GROUP BY review_reviewbit.field, review_review.instructor_id, courses_section.course_id, courses_course.semester;
            """
        )
        print(f"Inserted {cursor.rowcount} rows into PrecomputedReview")

        cursor.execute(
            """
            INSERT INTO review_precomputedreview (instructor_id, course_id, field, num_sections, average, semester)
            SELECT
                review_review.instructor_id as instructor_id,
                courses_section.course_id AS course_id,
                "final_enrollment" AS field,
                COUNT(review_review.section_id) AS num_sections,
                AVG(review_reviewbit.average) AS average,
                courses_course.semester AS semester
            FROM review_review
            INNER JOIN courses_section ON review_review.section_id = courses_section.id
            INNER JOIN courses_course ON courses_section.course_id = courses_course.id
            GROUP BY review_reviewbit.field, review_review.instructor_id, courses_section.course_id, courses_course.semester;
            """
        )

class Command(BaseCommand):
    help = """
    Deletes the precomputed_reviews table and repopulates it with the latest data.
    """

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        precompute_reviews()

