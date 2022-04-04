import json
import logging
import os
import re
from decimal import Decimal

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models.aggregates import Count
from django.db.models.expressions import Subquery, Value
from django.db.models.functions.comparison import Coalesce
from django.db.models.signals import post_save
from django.dispatch import receiver
from options.models import Option, get_value
from rest_framework.exceptions import APIException

from courses.models import (
    Building,
    Course,
    Department,
    Instructor,
    Meeting,
    Restriction,
    Room,
    Section,
    StatusUpdate,
    User,
)


logger = logging.getLogger(__name__)


def in_dev():
    return "PennCourses.settings.development" in os.environ["DJANGO_SETTINGS_MODULE"]


semester_suffix_map = {
    "A": "10",
    "B": "20",
    "C": "30",
}
semester_suffix_map_inv = {v: k for k, v in semester_suffix_map.items()}


def translate_semester(semester):
    """
    Translates a semester string (e.g. "2022C") to the format accepted by the new
    OpenData API (e.g. "202230").
    """
    if not semester:
        return None
    old_suffix = semester[-1].upper()
    if old_suffix not in semester_suffix_map:
        raise ValueError(
            f"Invalid semester suffix {old_suffix} (semester must have "
            "suffix A, B, or C; e.g. '2022C')."
        )
    return semester[:-1] + semester_suffix_map[old_suffix]


def translate_semester_inv(semester):
    """
    Translates a semester string in the format of the new OpenData API (e.g. "202230")
    to the format used by our backend (e.g. "2022C")
    """
    if not semester:
        return None
    new_suffix = semester[-2]
    if new_suffix not in semester_suffix_map_inv:
        raise ValueError(
            f"Invalid semester suffix {new_suffix} (semester must have "
            "suffix '10', '20', or '30'; e.g. '202230')."
        )
    return semester[:-2] + semester_suffix_map_inv[new_suffix]


def get_current_semester(allow_not_found=False):
    """
    This function retrieves the string value of the current semester, either from
    memory (if the value has been cached), or from the db (after which it will cache
    the value for future use). If the value retrieved from the db is None, an error is thrown
    indicating that the SEMESTER Option must be set for this API to work properly.
    You can prevent an error from being thrown (and cause the function to just return None
    in this case) by setting allow_not_found=True.
    The cache has a timeout of 25 hours, but is also invalidated whenever the SEMESTER Option
    is saved (which will occur whenever it is updated), using a post_save hook.
    See the invalidate_current_semester_cache function below to see how this works.
    """
    cached_val = cache.get("SEMESTER", None)
    if cached_val is not None:
        return cached_val

    retrieved_val = get_value("SEMESTER", None)
    if not allow_not_found and retrieved_val is None:
        raise APIException(
            "The SEMESTER runtime option is not set.  If you are in dev, you can set this "
            "option by running the command "
            "'python manage.py setoption SEMESTER 2020C', "
            "replacing 2020C with the current semester, in the backend directory (remember "
            "to run 'pipenv shell' before running this command, though)."
        )
    cache.set("SEMESTER", retrieved_val, timeout=90000)  # cache expires every 25 hours
    return retrieved_val


@receiver(post_save, sender=Option, dispatch_uid="invalidate_current_semester_cache")
def invalidate_current_semester_cache(sender, instance, **kwargs):
    """
    This function invalidates the cached SEMESTER value when the SEMESTER option is updated.
    """
    from courses.management.commands.load_add_drop_dates import load_add_drop_dates

    # ^ imported here to avoid circular imports

    if instance.key == "SEMESTER":
        cache.delete("SEMESTER")
        get_or_create_add_drop_period(instance.value)
        load_add_drop_dates()


def get_semester(datetime):
    """
    Given a datetime, estimate the semester of the period of course registration it occurred in.
    """
    if 3 <= datetime.month and datetime.month <= 9:
        return str(datetime.year) + "C"
    if datetime.month < 3:
        return str(datetime.year) + "A"
    return str(datetime.year + 1) + "A"


def get_add_drop_period(semester):
    """
    Returns the AddDropPeriod object corresponding to the given semester. Throws the same
    errors and behaves the same way as AddDropPeriod.objects.get(semester=semester) but runs faster.
    This function uses caching to speed up add/drop period object retrieval. Cached objects
    expire every 25 hours, and are also invalidated in the AddDropPeriod.save method.
    The add_drop_periods key in cache points to a dictionary mapping semester to add/drop period
    object.
    """
    from alert.models import AddDropPeriod  # imported here to avoid circular imports

    cached_adps = cache.get("add_drop_periods", dict())
    if semester not in cached_adps:
        cached_adps[semester] = AddDropPeriod.objects.get(semester=semester)
        cache.set("add_drop_periods", cached_adps, timeout=90000)  # cache expires every 25 hours
    return cached_adps[semester]


def get_or_create_add_drop_period(semester):
    """
    Behaves the same as get_add_drop_period if an AddDropPeriod object already exists for the given
    semester, and otherwise creates a new AddDropPeriod object for the given semester, returning
    the created object.
    """
    from alert.models import AddDropPeriod

    try:
        add_drop = get_add_drop_period(semester)
    except AddDropPeriod.DoesNotExist:
        add_drop = AddDropPeriod(semester=semester)
        add_drop.save()
    return add_drop


"""
Assumptions of our course code parsing regex:
    - Department code is 1-4 letters
    - Course code is (4 digits with an optional trailing letter) or (3 digits) or (3 letters)
    - Section code is 3 digits or 3 letters
"""
section_code_re = re.compile(
    r"^([A-Za-z]{1,4})\s*-?\s*(\d{4}[A-Za-z]?|\d{3}|[A-Za-z]{3})\s*-?\s*(\d{3}|[A-Za-z]{3})?$"
)


def separate_course_code(course_code, allow_partial=False):
    """
    Parse and return a (dept, course, section) ID tuple
    given a section full_code in any possible format.
    If allow_partial is True, then missing components will be returned as None.
    Otherwise, an incomplete match will raise a ValueError.
    """
    course_code = course_code.strip()
    match = section_code_re.match(course_code)
    if match:
        components = (match.group(1).upper(), match.group(2), match.group(3))
        if allow_partial or None not in components:
            return components
    raise ValueError(f"Course code could not be parsed: {course_code}")


def get_or_create_course(dept_code, course_id, semester):
    dept, _ = Department.objects.get_or_create(code=dept_code)
    return Course.objects.get_or_create(department=dept, code=course_id, semester=semester)


def get_or_create_course_and_section(course_code, semester, section_manager=None):
    if section_manager is None:
        section_manager = Section.objects
    dept_code, course_id, section_id = separate_course_code(course_code)

    course, course_c = get_or_create_course(dept_code, course_id, semester)
    section, section_c = section_manager.get_or_create(course=course, code=section_id)

    return course, section, course_c, section_c


def get_course_and_section(course_code, semester, section_manager=None):
    if section_manager is None:
        section_manager = Section.objects

    dept_code, course_id, section_id = separate_course_code(course_code)
    course = Course.objects.get(department__code=dept_code, code=course_id, semester=semester)
    section = section_manager.get(course=course, code=section_id)
    return course, section


def update_percent_open(section, new_status_update):
    """
    This function updates a section's percent_open field when a new status update is processed.
    """
    add_drop = get_or_create_add_drop_period(section.semester)
    last_status_update = section.last_status_update
    if new_status_update.created_at < add_drop.estimated_start:
        return
    if last_status_update is None:
        section.percent_open = Decimal(int(new_status_update.old_status == "O"))
        section.save()
    else:
        if last_status_update.created_at >= add_drop.estimated_end:
            return
        seconds_before_last = Decimal(
            max((last_status_update.created_at - add_drop.estimated_start).total_seconds(), 0)
        )
        seconds_since_last = Decimal(
            max(
                (
                    min(new_status_update.created_at, add_drop.estimated_end)
                    - max(last_status_update.created_at, add_drop.estimated_start)
                ).total_seconds(),
                0,
            )
        )
        section.percent_open = (
            Decimal(section.percent_open) * seconds_before_last
            + int(new_status_update.old_status == "O") * seconds_since_last
        ) / (seconds_before_last + seconds_since_last)
        section.save()


def record_update(section, semester, old_status, new_status, alerted, req, created_at=None):
    from alert.models import validate_add_drop_semester  # avoid circular imports

    u = StatusUpdate(
        section=section,
        old_status=old_status,
        new_status=new_status,
        alert_sent=alerted,
        request_body=req,
    )
    if created_at is not None:
        u.created_at = created_at
    u.save()

    valid_status_choices = dict(Section.STATUS_CHOICES).keys()

    def validate_status(name, status):
        if status not in valid_status_choices:
            raise ValidationError(
                f"{name} is invalid; expected a value in {valid_status_choices}, but got {status}"
            )

    validate_status("Old status", old_status)
    validate_status("New status", new_status)

    # Raises ValidationError if semester is not fall or spring (and correctly formatted)
    validate_add_drop_semester(semester)
    update_percent_open(section, u)

    return u


def set_instructors(section, instructors):
    instructor_obs = []
    for instructor in instructors:
        middle_initial = instructor["middle_initial"]
        if middle_initial:
            middle_initial += "."
        name_components = (
            instructor["first_name"],
            middle_initial,
            instructor["last_name"],
        )
        name = " ".join([c for c in name_components if c])
        penn_id = int(instructor["penn_id"])
        try:
            instructor_ob = Instructor.objects.filter(user_id=penn_id)[:1].get()
        except Instructor.DoesNotExist:
            try:
                user = User.objects.get(id=penn_id)
            except User.DoesNotExist:
                user = None
            instructor_ob, _ = Instructor.objects.get_or_create(
                name=name, defaults={"user": user}
            )  # TODO: save Penn ID
        instructor_obs.append(instructor_ob)
    section.instructors.set(instructor_obs)


def get_room(building_code, room_number):
    building, _ = Building.objects.get_or_create(code=building_code)
    room, _ = Room.objects.get_or_create(building=building, number=room_number)
    return room


def extract_date(date_str):
    if not date_str:
        return None
    date_str = date_str.split(" ")[0]
    if len(date_str.split("-")) != 3:
        return None
    return date_str


def clean_meetings(meetings):
    return {
        (m["days"], m["begin_time"], m["end_time"], m["building_code"], m["room_code"]): m
        for m in meetings
        if m["days"] and m["begin_time"] and m["end_time"]
    }.values()


def set_meetings(section, meetings):
    meetings = clean_meetings(meetings)

    meeting_times = [
        f"{meeting['days']} {meeting['begin_time']} - {meeting['end_time']}" for meeting in meetings
    ]
    section.meeting_times = json.dumps(meeting_times)

    section.meetings.all().delete()
    for meeting in meetings:
        online = (
            not meeting["building_code"]
            or not meeting["room_code"]
            or meeting.get("building_desc")
            and (
                meeting["building_desc"].lower() == "online"
                or meeting["building_desc"].lower() == "no room needed"
            )
        )
        room = None if online else get_room(meeting["building_code"], meeting["room_code"])
        start_time = Decimal(meeting["begin_time_24"]) / 100
        end_time = Decimal(meeting["end_time_24"]) / 100
        start_date = extract_date(meeting.get("start_date"))
        end_date = extract_date(meeting.get("end_date"))
        for day in list(meeting["days"]):
            Meeting(
                section=section,
                day=day,
                start=start_time,
                end=end_time,
                room=room,
                start_date=start_date,
                end_date=end_date,
            ).save()


def add_associated_sections(section, linked_sections):
    semester = section.course.semester
    section.associated_sections.clear()
    for s in linked_sections:
        subject_code = s.get("subject_code") or s.get("subject_code ")
        course_number = s.get("course_number") or s.get("course_number ")
        section_number = s.get("section_number") or s.get("section_number ")
        if not (subject_code and course_number and section_number):
            continue
        full_code = f"{subject_code}-{course_number}-{section_number}"
        _, associated, _, _ = get_or_create_course_and_section(full_code, semester)
        section.associated_sections.add(associated)


def set_crosslistings(course, crosslist_primary):
    if not crosslist_primary:
        course.primary_listing = course
    else:
        dept, course_code, _ = separate_course_code(crosslist_primary, allow_partial=True)
        primary_course, _ = get_or_create_course(dept, course_code, course.semester)
        course.primary_listing = primary_course


def add_restrictions(section, restrictions):
    for r in restrictions:
        rest, _ = Restriction.objects.get_or_create(
            code=r["registration_control_code"],
            defaults={"description": r["requirement_description"]},
        )
        section.restrictions.add(rest)


def upsert_course_from_opendata(info, semester):
    course_code = f"{info['course_department']}-{info['course_number']}-{info['section_number']}"
    course, section, _, _ = get_or_create_course_and_section(course_code, semester)

    course.title = info["course_title"] or ""
    course.description = info["course_description"] or ""
    # course.prerequisites = "\n".join(info["prerequisite_notes"])  # TODO: get prerequisite notes
    course.syllabus_url = info.get("syllabus_url") or None
    set_crosslistings(course, info["crosslist_primary"])

    try:
        min_cr = Decimal(info["minimum_credit"] or "0")
        max_cr = Decimal(info["maximum_credit"] or "0")
        section.credits = Decimal.max(min_cr, max_cr)
    except ValueError:
        section.credits = Decimal(0)

    section.capacity = int(info["max_enrollment"] or 0)
    section.activity = info["activity"] or "***"

    set_meetings(section, info["meetings"])

    set_instructors(section, info["instructors"])
    add_associated_sections(section, info["linked_courses"])

    # add_attributes(section, info["attributes"])  # TODO: save attributes (course or section?)
    # add_restrictions(section, info["restrictions"])  # TODO: add registration restrictions
    # add_grade_modes(section, info["grade_modes"])  # TODO: save grade modes

    section.save()
    course.save()


def update_course_from_record(update):
    section = update.section
    section.status = update.new_status
    section.save()


# averages review data for a given field, given a list of Review objects
def get_average_reviews(reviews, field):
    count = 0
    total = 0
    for r in reviews:
        try:
            rb = r.reviewbit_set.get(field=field)
            count += 1
            total += rb.average
        except ObjectDoesNotExist:
            pass
    if count == 0:
        raise ValueError("No reviews found for given field")
    return total / count


def subquery_count_distinct(subquery, column):
    """
    Returns a coalesced count of the number of distinct values in the specified column
    of the specified subquery. Usage example:
        Course.objects.annotate(
            num_activities=subquery_count_distinct(
                subquery=Section.objects.filter(course_id=OuterRef("id")),
                column="activity"
            )
        )  # counts the number of distinct activities each course has
    """
    return Coalesce(
        Subquery(
            subquery.annotate(common=Value(1))
            .values("common")
            .annotate(count=Count(column, distinct=True))
            .values("count")
        ),
        0,
    )


def does_object_pass_filter(obj, filter):
    """
    Returns True iff the given obj satisfies the given filter dictionary.
    Note that this only supports simple equality constraints (although it
    can traverse a relation to a single related object specified with double
    underscore notation). It does not support more complex filter conditions
    such as __gt.
    Example:
        does_object_pass_filter(obj, {"key": "value", "parent__key": "value2"})
    """
    for field, expected_value in filter.items():
        assert field != ""
        components = field.split("__")
        actual_value = getattr(obj, components[0])
        for component in components[1:]:
            actual_value = getattr(actual_value, component)
        if actual_value != expected_value:
            return False
    return True
