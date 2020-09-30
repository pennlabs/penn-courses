import uuid

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from tqdm import tqdm

from courses.models import Course, Instructor
from courses.util import (
    get_or_create_course,
    get_or_create_course_and_section,
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


def import_instructor(pennid, fullname, stat):
    """
    Given instructor info do one of a few things:
    1. Create a new instructor and user object and link the two
    2. Link together any existing instructors/users that should be linked together assuming the
       given pennid and fullname belong to the same person.
    """
    if pennid is not None:
        stat("instructors_with_pennid")

        user, user_created = User.objects.get_or_create(
            pk=int(pennid), defaults={"username": uuid.uuid4()}
        )
        if user_created:
            stat("users_created")
            user.set_unusable_password()
            user.save()

        if Instructor.objects.filter(user=user).exists():
            inst = Instructor.objects.get(user=user)
            inst_created = False
        elif Instructor.objects.filter(name=fullname).exists():
            inst = Instructor.objects.get(name=fullname)
            inst.user = user
            inst.save()
            inst_created = False
        else:
            try:
                inst = Instructor.objects.create(user=user, name=fullname)
            except IntegrityError:
                stat("instructor:integrity_error")
                return
            inst_created = True

        if inst_created:
            stat("instructors_created")

    elif len(fullname) > 0:
        inst, inst_created = Instructor.objects.get_or_create(name=fullname)
        if inst_created:
            stat("instructors_created")
    else:
        stat("instructors_without_info")
        inst = None

    return inst


def import_course_and_section(full_course_code, semester, course_title, primary_section_code, stat):
    """
    Given course and section info, update/create objects.
    """
    try:
        (course, section, course_created, section_created) = get_or_create_course_and_section(
            full_course_code, semester
        )
    except ValueError:
        stat("invalid_section_id")
        return None, None

    # Update course title if one isn't already set.
    course_dirty = False
    if course.title == "":
        course_dirty = True
        course.title = course_title

    # If no primary listing is set, add one.
    if primary_section_code is not None and course.primary_listing is None:
        try:
            dept, ccode, _ = separate_course_code(primary_section_code)
        except ValueError:
            stat("invalid_primary_section_id")
            return

        course.primary_listing, _ = get_or_create_course(dept, ccode, semester)
        course_dirty = True

    if course_dirty:
        stat("courses_updated")
        course.save()

    return course, section


def import_review(section, instructor, enrollment, responses, form_type, bits, stat):
    # Assumption: that all review objects for the semesters in question were
    # deleted before this runs.
    try:
        review = Review.objects.create(
            section=section,
            instructor=instructor,
            enrollment=enrollment,
            responses=responses,
            form_type=form_type,
        )
    except IntegrityError:
        stat("review:integrity_error")
        return
    review_bits = [ReviewBit(review=review, field=k, average=v) for k, v in bits.items()]

    # This saves us a bunch of database calls per row, since reviews have > 10 bits.
    try:
        ReviewBit.objects.bulk_create(review_bits)
    except IntegrityError:
        stat("reviewbit:integrity_error")
        return
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
            review_bits[slug] = row.get(col)

    import_review(
        section,
        inst,
        row.get("ENROLLMENT"),
        row.get("RESPONSES"),
        row.get("FORM_TYPE"),
        review_bits,
        stat,
    )

    # Attach instructor to course.
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

    ReviewBit.objects.update_or_create(
        review=review,
        field=field,
        defaults={
            "average": row.get("MEAN_TOTAL_RATING"),
            "median": row.get("MEDIAN_TOTAL_RATING"),
            "stddev": row.get("STANDARD_DEVIATION"),
            "rating0": row.get("TOTAL_RATING_0"),
            "rating1": row.get("TOTAL_RATING_1"),
            "rating2": row.get("TOTAL_RATING_2"),
            "rating3": row.get("TOTAL_RATING_3"),
            "rating4": row.get("TOTAL_RATING_4"),
        },
    )

    stat("detail_count")


def import_rows(rows, import_func, show_progress_bar=True):
    """
    Given a list of SQL rows, import them using the given import function
    """
    stats = dict()

    def stat(key, amt=1):
        """
        Helper function to keep track of how many rows we are adding to the DB,
        along with any errors in processing the incoming rows.
        """
        value = stats.get(key, 0)
        stats[key] = value + amt

    for row in tqdm(rows, disable=(not show_progress_bar)):
        import_func(row, stat)

    return stats


def import_summary_rows(summaries, show_progress_bar=True):
    return import_rows(summaries, import_summary_row, show_progress_bar)


def import_ratings_rows(ratings, show_progress_bar=True):
    return import_rows(ratings, import_ratings_row, show_progress_bar)


def import_description_rows(rows, semesters=None, show_progress_bar=True):
    descriptions = dict()

    stats = dict()

    def stat(key, amt=1):
        """
        Helper function to keep track of how many rows we are adding to the DB,
        along with any errors in processing the incoming rows.
        """
        value = stats.get(key, 0)
        stats[key] = value + amt

    for row in tqdm(rows, disable=(not show_progress_bar)):
        course_code = row.get("COURSE_ID")
        paragraph_num = row.get("PARAGRAPH_NUMBER")
        description_paragraph = row.get("COURSE_DESCRIPTION")

        desc = descriptions.get(course_code, dict())
        desc[int(paragraph_num)] = description_paragraph
        descriptions[course_code] = desc

    # The course_id we get from the description doesn't have a section code, which is needed
    # for separate_course_code.
    for course_id, paragraphs in tqdm(descriptions.items(), disable=(not show_progress_bar)):
        dept_code, course_code, _ = separate_course_code(course_id + "000")
        courses = Course.objects.filter(department__code=dept_code, code=course_code)

        if semesters is not None:
            courses = courses.filter(semester__in=semesters)

        paragraphs = list(paragraphs.items())
        paragraphs.sort(key=lambda x: x[0])
        description = "\n".join([p for _, p in paragraphs])
        courses.update(description=description)
