from tqdm import tqdm
from django.core.management.base import BaseCommand
from django.db import transaction
import django.utils.timezone as timezone

from courses.models import Course, Section
from courses.models import course_reviews, sections_with_reviews


REVIEW_FIELDS = [
    "course_quality",
    "difficulty",
    "instructor_quality",
    "work_required",
]

PREFIX = "calc_"


class Command(BaseCommand):
    help = "Calculates and persists review averages for Course and Section."

    def handle(self, *args, **options):
        self.stdout.write("Calculating Course review averages...")
        self.update_courses()
        self.stdout.write(self.style.SUCCESS("Finished calculating Course review averages."))

        self.stdout.write("Calculating Section review averages...")
        self.update_sections()
        self.stdout.write(self.style.SUCCESS("Finished calculating Section review averages."))

    def update_courses(self):
        queryset = course_reviews(
            Course.objects.all(),
            prefix=PREFIX,
        )

        courses_to_update = []

        for course in tqdm(queryset, desc="Updating Courses", file=self.stdout):
            for field in REVIEW_FIELDS:
                setattr(course, field, getattr(course, PREFIX + field))
            course.annotation_expiration = timezone.now + timezone.timedelta(days=30) 
            courses_to_update.append(course)

        with transaction.atomic():
            Course.objects.bulk_update(
                courses_to_update,
                REVIEW_FIELDS,
                batch_size=500,
            )

    def update_sections(self):
        queryset = sections_with_reviews(
            Section.objects.all(),
            prefix=PREFIX,
        )

        sections_to_update = []

        for section in tqdm(queryset, desc="Updating Sections", file=self.stdout):
            for field in REVIEW_FIELDS:
                setattr(section, field, getattr(section, PREFIX + field))
            section.annotation_expiration = timezone.now + timezone.timedelta(days=30)
            sections_to_update.append(section)

        with transaction.atomic():
            Section.objects.bulk_update(
                sections_to_update,
                REVIEW_FIELDS,
                batch_size=500,
            )
