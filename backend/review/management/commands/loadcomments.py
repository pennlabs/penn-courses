import csv

from django.core.management import BaseCommand
from tqdm import tqdm

from review.models import Review


def leftpad(num: int):
    if num < 10:
        return f"00{num}"
    elif num < 100:
        return f"0{num}"
    else:
        return f"{num}"


def get_semester(code):
    code = int(code)
    if code == 0:
        return "A"
    elif code == 1:
        return "B"
    elif code == 2:
        return "C"
    else:
        return "*"


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("path_to_csv", help="path to CSV file to use.")

    def handle(self, *args, **kwargs):
        with open(kwargs["path_to_csv"]) as csvfile:
            reader = csv.reader(csvfile)
            num_updated = 0
            lines = list(reader)
            for row in tqdm(lines):
                dept, course_id, section_id, year, semester_num, instructor_name, comment = row
                section_code = f"{dept}-{course_id}-{leftpad(int(section_id))}"
                semester = f"{year}{get_semester(semester_num)}"
                instructor_name = instructor_name.lower()
                num_updated += Review.objects.filter(
                    section__full_code=section_code,
                    section__course__semester=semester,
                    instructor__name__iexact=instructor_name,
                ).update(comments=comment)

            print(f"{num_updated} reviews updated.")
