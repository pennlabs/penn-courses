import csv
import os
import re
from textwrap import dedent

import jellyfish
from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from tqdm import tqdm

from courses.models import Course

TEST_SEMESTER = "2021C"

class Command(BaseCommand):
    help = dedent(
        """
        Scan for possibly incorrect course code mappings and output them to terminal sorted
        lexicographically first in terms of number of errors (using the Levenshtein distance metric)
        and then (if the --check_crosslistings flag is included) in order of what fraction of their
        crosslistings may also be erroneous.
        """
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--mapping_path",
            type=str,
            help=dedent(
                """
                The mapping_path argument should be the path to a csv with the first column being the old course code
                and the second being the corresponding new code.
                """
            ),
            nargs="?",
            default=None,
        )
        parser.add_argument(
            "--tolerance",
            type=int,
            help=dedent(
                """
                The tolerance argument should specify the minimum number of insertions, deletions
                or substitutions between the original course code and the new one to be reported as
                a potential error. Should be at least 1 since all 3 -> 4 digit mappings require at
                least 1 insertion. Note that setting tolerance value to a negative number may result
                in undesired behavior (such as mappings that are identical being output as different)
                """
            ),
            nargs="?",
            default=2,
        )
        parser.add_argument(
            "--check_crosslistings",
            help=dedent(
                """
                This flag should be included if you want to check crosslistings
                """
            ),
            default=False,
            action="store_true",
        )

    def handle(self, *args, **kwargs):
        # Read path
        src = os.path.abspath(kwargs["mapping_path"])
        _, file_extension = os.path.splitext(src)
        if not os.path.exists(src):
            return "File does not exist."
        if file_extension != ".csv":
            return "File is not a csv."

        error_mapping = {}
        error_list = []
        with open(src) as data_file:
            data_reader = csv.reader(data_file, delimiter=",", quotechar='"')
            for three_digit, four_digit in tqdm(data_reader, desc="Check mapping"):
                separated_three_digit = separate_course_code(three_digit)
                separated_four_digit = separate_course_code(four_digit)

                # Try some heuristic methods
                if separated_four_digit in heuristic_variations(separated_three_digit):
                    continue

                # If a mapping results in error greater than tolerance report it
                lev = jellyfish.levenshtein_distance(three_digit, four_digit)
                error_mapping[three_digit] = (four_digit, lev)

        # Check crosslistings for fraction of error & if crosslisting match
        if kwargs["check_crosslistings"]:
            for three_digit in tqdm(error_mapping, desc="Check crosslistings"):
                error_count = 0
                crosslisting_count = 0
                try:
                    course = Course.objects.get(full_code=three_digit, semester=TEST_SEMESTER) # TODO: replace TEST_SEMESTER
                except ObjectDoesNotExist:
                    continue
                for associated_code in course.crosslistings.values_list("full_code"):
                    crosslisting_count += 1
                    match error_mapping.get(associated_code):
                        case (_, error):
                            if error >= kwargs["tolerance"]:
                                error_count += 1
                        case _:
                            continue
                if crosslisting_count > 0:
                    error_fraction = error_count / crosslisting_count
                    error_mapping[three_digit] = error_mapping[three_digit] + (error_fraction,)

        # Sort
        for item in sorted(error_mapping.items(), key=lambda x: (x[0][1], x[0][2])):
            match item:
                case three_digit, (four_digit, lev, crosslisted_error_frac):
                    print(
                        f"{three_digit} -> {four_digit}: lev dist {lev} crosslisted error % {crosslisted_error_frac}"
                    )
                case three_digit, (four_digit, lev):
                    print(f"{three_digit} -> {four_digit}: lev dist {lev}")


def separate_course_code(course_code):
    """
    Return (dept, course) ID tuple given a course code in any
    possible format using either 3 or 4 digit course numbering.
    """
    course_regexes = [
        re.compile(r"([A-Za-z]+) *(\d{3,4})"),
        re.compile(r"([A-Za-z]+) *-(\d{3,4})"),
    ]
    course_code = course_code.replace(" ", "").upper()
    for regex in course_regexes:
        m = regex.match(course_code)
        if m is not None and len(m.groups()) >= 2:
            return m.group(1), m.group(2)
    raise ValueError(f"Course code could not be parsed: {course_code}")


def heuristic_variations(separated_three_digit_code):
    """Check a few simple variations on course codes"""
    course_number_variations = []
    course_number = separated_three_digit_code[1]
    # Add 0 to front
    course_number_variations.append("0" + course_number)
    # Add 0 to end
    course_number_variations.append(course_number + "0")
    # Repeat first digit
    course_number_variations.append(course_number[0] + course_number)
    variations = []
    for variation in course_number_variations:
        variations.append(
            separated_three_digit_code[:1] + (variation,) + separated_three_digit_code[2:]
        )
    return variations
