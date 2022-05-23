import json
import logging
import os
import re
import uuid
from decimal import Decimal

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import connection
from django.db.models.aggregates import Count
from django.db.models.expressions import Subquery, Value
from django.db.models.functions.comparison import Coalesce
from django.db.models.signals import post_save
from django.dispatch import receiver
from options.models import Option, get_value
from rest_framework.exceptions import APIException

from courses.models import (
    Attribute,
    Building,
    Course,
    Department,
    Instructor,
    Meeting,
    NGSSRestriction,
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
    new_suffix = semester[-2:]
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


def get_set_id(obj):
    """
    Returns the next ID for the given object (which hasn't yet been created).
    """
    if obj.id:
        return obj.id
    # Source: https://djangosnippets.org/snippets/10474/
    with connection.cursor() as cursor:
        # NOTE: this relies on PostgreSQL-specific details for autoincrement
        # https://www.postgresql.org/docs/9.4/functions-sequence.html
        cursor.execute(
            "SELECT nextval('{0}_{1}_{2}_seq'::regclass)".format(
                obj._meta.app_label.lower(),
                obj._meta.object_name.lower(),
                obj._meta.pk.name,
            )
        )
        obj.id = obj.pk = cursor.fetchone()[0]
        return obj.pk


def is_fk_set(obj, fk_field):
    """
    Returns true if the specified foreign key field has been
    set on the given object, false otherwise.
    """
    return bool(getattr(obj, fk_field, None) or getattr(obj, fk_field + "_id", None))


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


def get_or_create_course(dept_code, course_id, semester, defaults=None):
    dept, _ = Department.objects.get_or_create(code=dept_code)
    return Course.objects.get_or_create(
        department=dept, code=course_id, semester=semester, defaults=defaults
    )


def get_or_create_course_and_section(
    course_code, semester, section_manager=None, course_defaults=None, section_defaults=None
):
    if section_manager is None:
        section_manager = Section.objects
    dept_code, course_id, section_id = separate_course_code(course_code)

    course, course_c = get_or_create_course(
        dept_code, course_id, semester, defaults=course_defaults
    )
    section, section_c = section_manager.get_or_create(
        course=course, code=section_id, defaults=section_defaults
    )

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


def merge_instructors(user, name):
    """
    Merge the instructor corresponding to the given user into the
    instructor with the given name, if both exist.
    """
    from review.management.commands.mergeinstructors import resolve_duplicates

    def stat(key, amt=1, element=None):
        return

    try:
        user_instructor = Instructor.objects.get(user=user)
        name_instructor = Instructor.objects.get(name=name)
        duplicates = {user_instructor, name_instructor}
        if len(duplicates) == 1:
            return
        resolve_duplicates([duplicates], dry_run=False, stat=stat)
    except Instructor.DoesNotExist:
        pass


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
            merge_instructors(User.objects.get(id=penn_id), name)
            instructor_ob = Instructor.objects.get(user_id=penn_id)
            instructor_ob.name = name
            instructor_ob.save()
        except (Instructor.DoesNotExist, User.DoesNotExist):
            user, user_created = User.objects.get_or_create(
                id=penn_id, defaults={"username": uuid.uuid4()}
            )
            if user_created:
                user.set_unusable_password()
                user.save()
            instructor_ob, _ = Instructor.objects.get_or_create(name=name)
            instructor_ob.user = user
            instructor_ob.save()
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
        (
            tuple(sorted(list(set(m["days"])))),
            m["begin_time"],
            m["end_time"],
            m["building_code"],
            m["room_code"],
        ): m
        for m in meetings
        if m["days"] and m["begin_time"] and m["end_time"]
    }.values()


def set_meetings(section, meetings):
    meetings = clean_meetings(meetings)

    for meeting in meetings:
        meeting["days"] = "".join(sorted(list(set(meeting["days"]))))
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
            Meeting.objects.get_or_create(
                section=section,
                day=day,
                start=start_time,
                end=end_time,
                room=room,
                defaults={
                    "start_date": start_date,
                    "end_date": end_date,
                },
            )


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


def set_crosslistings(course, crosslistings):
    if not crosslistings:
        course.primary_listing = course
        return
    for crosslisting in crosslistings:
        if crosslisting["is_primary_section"]:
            primary_course, _ = get_or_create_course(
                crosslisting["subject_code"], crosslisting["course_number"], course.semester
            )
            course.primary_listing = primary_course
            return


def upsert_course_from_opendata(info, semester, missing_sections=None):
    dept_code = info.get("subject") or info.get("course_department")
    assert dept_code, json.dumps(info, indent=2)
    course_code = f"{dept_code}-{info['course_number']}-{info['section_number']}"
    course, section, _, _ = get_or_create_course_and_section(course_code, semester)

    course.title = info["course_title"] or ""
    course.description = (info["course_description"] or "").strip()
    if info.get("additional_section_narrative"):
        course.description += (course.description and "\n") + info["additional_section_narrative"]
    # course.prerequisites = "\n".join(info["prerequisite_notes"])  # TODO: get prerequisite info
    course.syllabus_url = info.get("syllabus_url") or None

    # set course primary listing
    set_crosslistings(course, info["crosslistings"])

    section.crn = info["crn"]
    section.credits = Decimal(info["credits"] or "0") if "credits" in info else None
    section.capacity = int(info["max_enrollment"] or 0)
    section.activity = info["activity"] or "***"

    set_meetings(section, info["meetings"])

    set_instructors(section, info["instructors"])
    add_associated_sections(section, info["linked_courses"])

    # delete all attributes and restrictions
    Attribute.objects.all().delete()
    NGSSRestriction.objects.all().delete()

    add_attributes(section, info["attributes"])
    add_restrictions(section, info["course_restrictions"])
    # add_grade_modes(section, info["grade_modes"])  # TODO: save grade modes

    section.save()
    course.save()

    if missing_sections:
        missing_sections.discard(section.full_code)


def add_attributes(section, attributes):
    """
    Add attributes to course of section.
    Create attribute if it does not exist
    """
    for attribute in attributes:
        try:
            attr = Attribute.objects.get(
                code=attribute.get("attribute_code"),
            )
        except ObjectDoesNotExist:
            school = identify_school(attribute.get("attribute_code"))
            attr = Attribute.objects.create(
                code=attribute.get("attribute_code"),
                description=attribute.get("attribute_desc"),
                school=school,
            )
        attr.courses.add(section.course)


def identify_school(attribute_code):
    """
    Determine the school short code (defined in the Attribute model's SCHOOL_CHOICES attribute)
    based on the first one or two letters of attribute_code
    :param attribute_code: the attribute's attribute_code
    :return: the short code representing the school this attribute fits in (may be "OTHER"
        if none of these heuristics apply)
    """
    prefix_to_school = {
        "A": "SAS",
        "B": "LPS",
        "E": "SEAS",
        "F": "DSGN",
        "G": "GSE",
        "L": "LAW",
        "MM": "MED",
        "Q": "MODE",
        "V": "VET",
        "N": "NUR",
        "W": "WH"
    }
    for prefix, school in prefix_to_school.items():
        if attribute_code.startswith(prefix):
            return school
    return "OTHER"


def add_restrictions(section, restrictions):
    """
    Add restrictions to course of section.
    Create restriction if it does not exist.
    """
    for restriction in restrictions:
        try:
            res = Attribute.objects.get(
                code=restriction.get("restriction_code"),
            )
        except ObjectDoesNotExist:
            res = NGSSRestriction.objects.create(
                code=restriction.get("restriction_code"),
                description=restriction.get("restriction_desc"),
                restriction_type=restriction.get("restriction_type"),
                include_or_exclude=restriction.get("incl_excl_ind") == "E",
            )
        res.courses.add(section.course)


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
