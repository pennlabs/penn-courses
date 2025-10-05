import gc

from django.contrib.auth import get_user_model
from tqdm import tqdm

from courses.models import Course
from courses.util import (
    get_or_create_course,
    get_or_create_course_and_section,
    import_instructor,
    separate_course_code,
)
from review.models import COLUMN_TO_SLUG, CONTEXT_TO_SLUG, Review, ReviewBit
from review.util import titleize


"""
PCR SQL DUMP IMPORT FUNCTIONS

The functions in this file represent the "back-end" of the PCR data import.
Dictionaries representing rows of PCR data come in and are written to the proper
database objects. Care is taken not to duplicate rows by using get_or_create().

Helper functions for importing instructors, sections, courses and reviews take in
specific values extracted from dictionaries. This allows for re-use between import
passes (for example, the SUMMARY file and the CROSSLISTINGS file), as well as allowing for
more granular unit tests.
"""

User = get_user_model()


def filter_by_term(rows, semesters, semester_key="TERM"):
    return [row for row in rows if row[semester_key] in semesters]


def import_course_and_section(full_course_code, semester, course_title, primary_section_code, stat):
    """
    Given course and section info, update/create objects.
    """
    primary_listing = None
    if primary_section_code:
        try:
            dept, ccode, _ = separate_course_code(primary_section_code)
        except ValueError:
            stat("invalid_primary_section_id")
            return
        primary_listing, _ = get_or_create_course(dept, ccode, semester)

    try:
        course, section, _, _ = get_or_create_course_and_section(
            full_course_code,
            semester,
            course_defaults={
                "primary_listing": primary_listing,
                "title": course_title or "",
            },
        )
    except ValueError:
        stat("invalid_section_id")
        return None, None

    # Update course title if one isn't already set.
    if course_title and not course.title:
        course.title = course_title
        course.save()
        stat("courses_updated")

    return course, section


def import_review(section, instructor, enrollment, responses, form_type, bits, stat):
    # Assumption: that all review objects for the semesters in question were
    # deleted before this runs.
    review, created = Review.objects.get_or_create(
        section=section,
        instructor=instructor,
        defaults={
            "enrollment": enrollment,
            "responses": responses,
            "form_type": form_type,
        },
    )
    if not created:
        stat("duplicate_review")
    review_bits = []
    for key, value in bits.items():
        if value is None or value == "null":
            stat(f"null value for {key}")
            continue
        review_bits.append(ReviewBit(review=review, field=key, average=value))

    # This saves us a bunch of database calls per row, since reviews have > 10 bits.
    ReviewBit.objects.bulk_create(review_bits, ignore_conflicts=True)
    stat("reviewbit_created_count", len(review_bits))


def import_summary_row(row, stat):
    # Import instructor.
    pennid = row.get("INSTRUCTOR_PENN_ID")
    firstname = row.get("INSTRUCTOR_FNAME", "")
    lastname = row.get("INSTRUCTOR_LNAME", "")
    fullname = titleize(f"{firstname} {lastname}").strip()
    inst = import_instructor(pennid, fullname, stat)

    # Import course and section.
    full_course_code = row.get("SECTION_ID")
    semester = row.get("TERM")
    if full_course_code is None:
        stat("no_course_code")
        return

    if semester is None:
        stat("no_semester")
        return

    course_title = titleize(row.get("TITLE", ""))
    primary_section_code = row.get("PRI_SECTION")
    course, section = import_course_and_section(
        full_course_code, semester, course_title, primary_section_code, stat
    )
    if course is None or section is None:
        return

    # Get ReviewBit averages.
    review_bits = {}
    for col, slug in COLUMN_TO_SLUG.items():
        if col in row:
            if row.get(col) is not None and row.get(col) != "":
                review_bits[slug] = float(row.get(col))
            else:
                review_bits[slug] = None

    import_review(
        section,
        inst,
        int(row.get("ENROLLMENT")),
        int(row.get("RESPONSES")),
        row.get("FORM_TYPE"),
        review_bits,
        stat,
    )

    # Attach instructor to course.
    if inst is not None:
        section.instructors.add(inst)

    # We finished importing this row!
    stat("row_count")


def import_ratings_row(row, stat):
    context = row.get("CONTEXT_NAME")
    if context is None:
        stat("no_context_field")
        return

    pennid = row.get("INSTRUCTOR_PENN_ID")
    name = row.get("INSTRUCTOR_NAME", "")
    parts = name.split(",")
    if len(parts) > 1:
        fullname = titleize(f"{parts[1]} {parts[0]}").strip()
    elif len(parts) == 1:
        fullname = titleize(name).strip()
    inst = import_instructor(pennid, fullname, stat)

    full_course_code = row.get("SECTION_ID")
    semester = row.get("TERM")
    if full_course_code is None:
        stat("no_course_code")
        return

    if semester is None:
        stat("no_semester")
        return

    course_title = titleize(row.get("TITLE", ""))
    course, section = import_course_and_section(
        full_course_code, semester, course_title, None, stat
    )

    if course is None or section is None:
        return

    # ratings_row assumes that summary_row has already created a Review model for this review.
    try:
        review = Review.objects.get(section=section, instructor=inst)
    except Review.DoesNotExist:
        stat("summary_missing")
        return

    field = CONTEXT_TO_SLUG.get(context)
    if field is None:
        stat(f"missing slug for '{context}'")
        return

    details = {
        "average": row.get("MEAN_TOTAL_RATING"),
        "median": row.get("MEDIAN_TOTAL_RATING"),
        "stddev": row.get("STANDARD_DEVIATION"),
        "rating0": row.get("TOTAL_RATING_0"),
        "rating1": row.get("TOTAL_RATING_1"),
        "rating2": row.get("TOTAL_RATING_2"),
        "rating3": row.get("TOTAL_RATING_3"),
        "rating4": row.get("TOTAL_RATING_4"),
    }

    for key, val in details.items():
        if val is None or val == "null":
            stat(f"null value for {key}")
            return

    ReviewBit.objects.update_or_create(
        review=review,
        field=field,
        defaults=details,
    )

    stat("detail_count")


def gen_stat(stats):
    """
    Generates a stat function for a given stats dict.
    """

    def stat(key, amt=1):
        """
        Helper function to keep track of how many rows we are adding to the DB,
        along with any errors in processing the incoming rows.
        """
        value = stats.get(key, 0)
        stats[key] = value + amt

    return stat


def import_summary_rows(summaries: iter, show_progress_bar=True):
    """
    Imports summary rows given a summaries iterable.
    """
    stats = dict()
    stat = gen_stat(stats)
    for row in tqdm(summaries, disable=(not show_progress_bar)):
        import_summary_row(row, stat)
    return stats


def import_ratings_rows(num_ratings, ratings, semesters=None, show_progress_bar=True):
    """
    Imports rating rows given an iterator ratings and total number of rows num_ratings.
    Optionally filter rows to import by semester with the given semesters list.
    """
    stats = dict()
    stat = gen_stat(stats)
    for i, row in tqdm(enumerate(ratings), total=num_ratings, disable=(not show_progress_bar)):
        if i % 10000 == 0:
            gc.collect()
        if semesters is None or row["TERM"] in semesters:
            import_ratings_row(row, stat)
    return stats


def import_description_rows(num_rows, rows, semesters=None, show_progress_bar=True):
    """
    Imports description rows given an iterator rows and total number of rows num_rows.
    Optionally filter courses for which to update descriptions by semester with the
    given semesters list.
    """
    descriptions = dict()

    for row in tqdm(rows, total=num_rows, disable=(not show_progress_bar)):
        course_code = row.get("COURSE_ID")
        paragraph_num = row.get("PARAGRAPH_NUMBER")
        description_paragraph = row.get("COURSE_DESCRIPTION")

        desc = descriptions.get(course_code, dict())
        desc[int(paragraph_num)] = description_paragraph
        descriptions[course_code] = desc

    for course_id, paragraphs in tqdm(descriptions.items(), disable=(not show_progress_bar)):
        dept_code, course_code, _ = separate_course_code(course_id, allow_partial=True)
        if course_code is None:
            continue
        # Don't replace descriptions which are already present (from registrar import, most likely).
        courses = Course.objects.filter(
            department__code=dept_code, code=course_code, description=""
        )

        if semesters is not None:
            courses = courses.filter(semester__in=semesters)

        paragraphs = list(paragraphs.items())
        paragraphs.sort(key=lambda x: x[0])
        description = "\n".join([p for _, p in paragraphs])
        courses.update(description=description)
