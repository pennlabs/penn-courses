import itertools
import json
import logging
import os
import random
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
from review.management.commands.mergeinstructors import resolve_duplicates


logger = logging.getLogger(__name__)


def in_dev():
    return "PennCourses.settings.development" in os.environ["DJANGO_SETTINGS_MODULE"]


semester_suffix_map = {
    "A": "10",
    "B": "20",
    "C": "30",
}
semester_suffix_map_inv = {v: k for k, v in semester_suffix_map.items()}
semester_suffix_map_hum = {"A": "Spring", "B": "Summer", "C": "Fall"}


semester_pattern = re.compile(r"^(\d{4})([ABC])$")
path_semester_pattern = re.compile(r"^(\d{4})(10|20|30)$")


def translate_semester(semester, ignore_error=False):
    """
    Translates a semester string (e.g., "2022C") to the format accepted by
    the new OpenData API (e.g., "202230").
    """
    if semester is None:
        return None

    match = semester_pattern.match(semester)
    if not match:
        if ignore_error:
            return semester
        raise ValueError(f"Invalid semester '{semester}' (should be of the form '2022C').")

    year, suffix = match.groups()
    return year + semester_suffix_map[suffix]


def translate_semester_inv(semester, ignore_error=False):
    """
    Translates a semester string in the format of Path / Banner / OpenData (e.g., "202230")
    to the format used by our backend (e.g., "2022C")
    """
    if semester is None:
        return None

    match = path_semester_pattern.match(semester)
    if not match:
        if ignore_error:
            return semester
        raise ValueError(f"Invalid semester '{semester}' (should be of the form '202210').")

    year, suffix = match.groups()
    return year + semester_suffix_map_inv[suffix]


def normalize_semester(semester):
    """
    Translates a semester from Path format (e.g. "202230")
    to to the format used by our backend (e.g. "2022C"),
    or leaves the same if not in Path format.
    """
    return translate_semester_inv(semester, ignore_error=True) or semester


def prettify_semester(semester):
    """
    Translates a semester in either Path format (e.g. "202230") or internal format
    (e.g. "2022C") to human readable format (e.g. "Fall 2022").
    """
    if semester is None:
        return None

    semester = normalize_semester(semester)

    match = semester_pattern.match(semester)
    if not match:
        raise ValueError(f"Invalid semester '{semester}'.")

    year, suffix = match.groups()
    return f"{semester_suffix_map_hum[suffix]} {year}"


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


def get_course_and_section(course_code_or_crn, semester, section_manager=None):
    if section_manager is None:
        section_manager = Section.objects

    try:
        dept_code, course_id, section_id = separate_course_code(str(course_code_or_crn))
        course = Course.objects.get(department__code=dept_code, code=course_id, semester=semester)
        section = section_manager.get(course=course, code=section_id)
    except ValueError:
        section = (
            section_manager.prefetch_related("course")
            .exclude(status="X")
            .get(crn=course_code_or_crn, course__semester=semester)
        )
        course = section.course
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


def import_instructor(pennid, name, stat=None):
    if not stat:
        stat = lambda key, amt=1, element=None: None  # noqa E731
    if not pennid:
        instructor_ob = Instructor.objects.filter(name=name).order_by("-updated_at").first()
        if not instructor_ob:
            stat("instructors_created")
            instructor_ob = Instructor.objects.create(name=name)
    else:
        try:
            instructor_ob = Instructor.objects.get(user_id=pennid)
            if instructor_ob.name != name:
                stat("instructor_names_updated")
                instructor_ob.name = name
                instructor_ob.save()
        except Instructor.DoesNotExist:
            user, user_created = User.objects.get_or_create(
                id=pennid, defaults={"username": uuid.uuid4()}
            )
            if user_created:
                stat("users_created")
                user.set_unusable_password()
                user.save()
            instructor_ob = (
                Instructor.objects.filter(name=name, user__isnull=True)
                .order_by("-updated_at")
                .first()
            )
            if instructor_ob:
                stat("instructor_users_updated")
                instructor_ob.user = user
                instructor_ob.save()
            else:
                stat("instructors_created")
                instructor_ob = Instructor.objects.create(user=user, name=name)
    dups = set(Instructor.objects.filter(name=name, user__isnull=True)) | {instructor_ob}
    if len(dups) > 1:
        resolve_duplicates(
            [dups],
            dry_run=False,
            stat=stat,
        )
    return instructor_ob


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
        pennid = int(instructor["penn_id"])
        instructor_obs.append(import_instructor(pennid, name))
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
            meeting = Meeting.objects.update_or_create(
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
    course.syllabus_url = info.get("syllabus_url") or None

    # set course primary listing
    set_crosslistings(course, info["crosslistings"])

    section.crn = info["crn"]
    section.credits = Decimal(info["credits"] or "0") if "credits" in info else None
    section.code_specific_enrollment = int(info["section_enrollment"] or 0)
    section.code_specific_capacity = int(info["max_enrollment"] or 0)
    section.capacity = int(info["max_enrollment_crosslist"] or section.code_specific_capacity)
    section.activity = info["activity"] or ""

    set_meetings(section, info["meetings"])

    set_instructors(section, info["instructors"])
    add_associated_sections(section, info["linked_courses"])
    add_restrictions(section, info["course_restrictions"])

    add_attributes(course, info["attributes"])

    section.save()
    course.save()

    if missing_sections:
        missing_sections.discard(section.id)


def add_attributes(course, attributes):
    """
    Clear attributes of a course and add new ones.
    Create attribute if it does not exist
    """
    course.attributes.clear()
    for attribute in attributes:
        school = identify_school(attribute.get("attribute_code"))
        desc = attribute.get("attribute_desc")
        attr, _ = Attribute.objects.update_or_create(
            code=attribute.get("attribute_code"),
            defaults={"description": desc, "school": school},
        )
        attr.courses.add(course)


def identify_school(attribute_code):
    """
    Determine the school short code (defined in the Attribute model's SCHOOL_CHOICES attribute)
    based on the first one or two letters of attribute_code
    :param attribute_code: the attribute's attribute_code
    :return: the short code representing the school this attribute fits in or None
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
        "W": "WH",
    }
    for prefix, school in prefix_to_school.items():
        if attribute_code.startswith(prefix):
            return school
    return None


def add_restrictions(section, restrictions):
    """
    Add restrictions to section.
    Create restriction if it does not exist.
    """
    for restriction in restrictions:
        code = restriction.get("restriction_code")
        description = restriction.get("restriction_desc")
        restriction_type = restriction.get("restriction_type")
        inclusive = restriction.get("incl_excl_ind") == "I"
        res, _ = NGSSRestriction.objects.update_or_create(
            code=code,
            defaults={
                "description": description,
                "restriction_type": restriction_type,
                "inclusive": inclusive,
            },
        )
        section.ngss_restrictions.add(res)


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

def historical_year_probability(current, courses):
    prob_distribution = [0.4, 0.3, 0.15, 0.1, 0.05]
    def get_semester_and_course_index(semester):
        semester_letter = semester[-1]
        semester_number = 0
        if semester_letter == "A":
            semester_number = 1
        elif semester_letter == "B":
            semester_number = 2
        elif semester_letter == "C":
            semester_number = 3
        semester_year = int(semester[:-1])
        return (10*semester_year + semester_number)
    current_index = get_semester_and_course_index(current)
    min_index = current_index - 50
    max_index = current_index - 10
    p_A = 0
    p_B = 0
    p_C = 0
    for c in courses:
        index = get_semester_and_course_index(c.semester)
        if index < min_index or index > max_index:
            continue
        diff = (max_index - index)+9//10
        if index % 10 == 1:
            p_A += prob_distribution[diff]
        elif index % 10 == 2:
            p_B += prob_distribution[diff]
        elif index % 10 == 3:
            p_C += prob_distribution[diff]
    return [p_A, p_B, p_C]




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


def all_semesters() -> set[str]:
    return set(Course.objects.values_list("semester", flat=True).distinct())


def get_semesters(semesters: str = None) -> list[str]:
    """
    Validate a given string semesters argument, and return a list of the individual string semesters
    specified by the argument.
    Expects a comma-separated string of semesters, or "all" to return all semesters in the DB.
    Defaults to the current semester only.
    """
    possible_semesters = all_semesters()
    if semesters is None:
        semesters = [get_current_semester()]
    elif semesters == "all":
        semesters = list(possible_semesters)
    else:
        semesters = semesters.strip().split(",")
        for s in semesters:
            if s not in possible_semesters:
                raise ValueError(f"Provided semester {s} was not found in the db.")
    return sorted(semesters)

def find_possible_schedules(
    courses, count=None, breaks={"M": [], "T": [], "W": [], "R": [], "F": []}
):
    """
    Given a list of courses, returns a list of all possible schedules
    that can be made from those courses.
    If a count is specified, returns only schedules with that many courses.
    """

    day_to_num = {"M": 0, "T": 1, "W": 2, "R": 3, "F": 4}
    whitelist = ["CIS-7000"]

    class Scheduler:
        def __init__(self):
            self.intervals = []

        def add_interval(self, start_time, end_time, class_name, section, credit):
            # Adds an interval to the list of intervals
            self.intervals.append((start_time, end_time, class_name, section, credit))
            return True

        def find_optimal_schedule(self, unwanted_intervals=[]):
            # Sort intervals by end time
            sorted_intervals = sorted(self.intervals, key=lambda x: x[1])
            # Remove unwanted intervals
            not_ok = []
            for unwanted_interval in unwanted_intervals:
                [
                    not_ok.append(interval[3])
                    for interval in sorted_intervals
                    if not (
                        interval[0] > unwanted_interval[1] or interval[1] < unwanted_interval[0]
                    )
                ]
            sorted_intervals = [
                interval for interval in sorted_intervals if not (interval[3] in not_ok)
            ]
            # Initialize variables
            n = len(sorted_intervals)
            dp = [1] * n
            prev = [-1] * n
            # Iterate over sorted intervals
            for i in range(1, n):
                for j in range(i):
                    if (sorted_intervals[j][1] <= sorted_intervals[i][0]) and (
                        sorted_intervals[j][2] != sorted_intervals[i][2]
                    ):
                        if dp[j] + 1 > dp[i]:
                            dp[i] = dp[j] + 1
                            prev[i] = j
            # Find the maximum number of non-overlapping intervals
            if dp:
                max_intervals = max(dp)
            else:
                return []
            # Find the index of the last interval in the optimal schedule
            last_interval_index = dp.index(max_intervals)
            # Build the optimal schedule by backtracking through the prev array
            optimal_schedule = []
            while last_interval_index != -1:
                optimal_schedule.append(sorted_intervals[last_interval_index])
                last_interval_index = prev[last_interval_index]
            optimal_schedule.reverse()
            # Select only one section for each class in the optimal schedule
            selected_classes = set()
            final_schedule = []
            for interval in optimal_schedule:
                class_name = interval[2]
                sections = [i for i in optimal_schedule if i[2] == class_name]
                if class_name not in whitelist:
                    section = random.choice(sections)
                    if class_name not in selected_classes:
                        selected_classes.add(class_name)
                        final_schedule.append(section)
                else:
                    selected_classes.add(class_name)
                    final_schedule += sections
            return final_schedule

    def find_sections(courses):
        """
        Separates the lectures and recitations of a certain course into a hash map
        """
        course_to_sections = {}
        for course in courses.keys():
            course_to_sections[course] = {
                "LEC": [section for section in courses[course] if section["activity"] == "LEC"],
                "REC": [section for section in courses[course] if section["activity"] == "REC"],
            }
        return course_to_sections

    def find_activities(c_to_s, activity):
        """
        Given a dictionary of courses and their sections,
        returns a list of only the activities of a certain type (ex: LEC).

        Parameters:
        c_to_s (dict): A dictionary of courses and their sections.
        activity (str): The type of activity to filter by (ex: LEC).

        Returns:
        list: A list of activities of the specified type.
        """
        activities = []
        for key in c_to_s.keys():
            activities.append(c_to_s[key][activity])
        return activities

    def find_lectures_on_day(lectures, day):
        """
        Finds all the lectures on a given day.

        Parameters:
            lectures (list): A list of lectures.
            day (str): The day to search for lectures on.

        Returns:
            list: A list of tuples containing the start time, end time,
            course code, and section ID for each lecture on the given day.
        """
        lectures_on_day = []
        for lecture in lectures:
            for section in lecture:
                for meeting in section["meetings"]:
                    if meeting["day"] == day:
                        # Adds a randomizer to randomize the order they are fed to the scheduler
                        lectures_on_day.append(
                            (
                                float(meeting["start"]),
                                float(meeting["end"]) + 0.001 * random.random(),
                                "-".join(section["id"].split("-")[0:2]),
                                section["id"],
                                section["credits"],
                            )
                        )
        return lectures_on_day

    def schedule_to_section(schedules):
        """
        Given a list of schedules,
        returns a list of sections by stripping the time intervals from the schedule list.

        Parameters:
            schedules (list): A list of schedules.

        Returns:
            list: A list of sections.
        """
        # Removes the time intervals from the schedule list
        sections = []
        for s in schedules:
            sections.append((s[3], s[4]))
        return sections

    def remove_duplicates(given_l):
        """
        Removes duplicates from a list.
        Example:
        remove_duplicates([1,1,1,3,5,7,7]) = [1,3,5,7]
        """
        newl = []
        [newl.append(x) for x in given_l if x not in newl]
        return newl

    def choose_class_hash(given_l):
        """
        Given a list of section nodes, chooses one section per class from each schedule randomly.

        Parameters:
            l (list): A list of section nodes.

        Returns:
            list: A list of chosen sections, one per class.
        """
        hash = {}
        courses = []
        for node in given_l:
            class_name = "-".join(node[0].split("-")[0:2])
            if class_name not in hash.keys():
                hash[class_name] = [node]
            else:
                hash[class_name].append(node)
        for key in hash.keys():
            # Chooses a random lecture for each class
            if key not in whitelist:
                courses.append(random.choice(hash[key]))
            else:
                courses += hash[key]
        return courses

    def credit_count(sections):
        acc = 0
        for section in sections:
            acc += section[1]
        return acc

    def check_if_schedule_possible(schedule, courses, unwanted_intervals):
        """
        Given a schedule and a list of courses,
        checks if the schedule is possible by ensuring that there are no time conflicts
        between the meetings of the courses in the schedule.

        Parameters:
            schedule (list): A list of section IDs representing the courses in the schedule.
            courses (list): A list of dictionaries representing the courses,
            where each dictionary contains a list of sections.

        Returns:
            bool: True if the schedule is possible, False otherwise.
        """
        if schedule == []:
            return False
        intervals = []
        for course in courses:
            for section in course:
                if (section["id"], section["credits"]) in schedule:
                    for meeting in section["meetings"]:
                        intervals.append(
                            (
                                day_to_num[meeting["day"]] + 0.01 * float(meeting["start"]),
                                day_to_num[meeting["day"]] + 0.01 * float(meeting["end"]),
                                section["id"],
                                section["credits"],
                            )
                        )
        intervals = sorted(intervals, key=lambda x: x[0])
        not_ok = []
        unwanted = []
        for day in unwanted_intervals.keys():
            for break_i in unwanted_intervals[day]:
                unwanted.append(
                    (
                        day_to_num[day] + 0.01 * float(break_i[0]),
                        day_to_num[day] + 0.01 * float(break_i[1]),
                    )
                )
        for unwanted_interval in unwanted:
            [
                not_ok.append(interval[2])
                for interval in intervals
                if not (interval[0] > unwanted_interval[1] or interval[1] < unwanted_interval[0])
            ]
        if len(not_ok) > 0:
            return False
        for i in range(len(intervals)):
            if i == 0:
                continue
            if intervals[i][0] < intervals[i - 1][1]:
                return False
        return True

    def scheduler_for_day(lectures, day, breaks):
        """
        Takes a list of lectures and a day of week,
        and returns a list of unique schedules for that day.
        The schedules are generated by taking 10 samples of possible schedules
        based on the dynamic programming algorithm.
        """
        day_classes = find_lectures_on_day(lectures, day)
        scheduler = Scheduler()
        for day_class in day_classes:
            scheduler.add_interval(
                day_class[0], day_class[1], day_class[2], day_class[3], day_class[4]
            )
        day_schedules = []
        for _ in range(5):
            day_schedules.append(scheduler.find_optimal_schedule(breaks[day]))
        day_schedules_unique = remove_duplicates(day_schedules)
        return day_schedules_unique

    def add_recs_to_schedule(schedule, recs, lectures, breaks):
        """
        Bruteforces recitations into the schedule based on the lectures.

        Parameters:
            schedule (list): A list of strings representing the current schedule.
            recs (list): A list of lists, where each inner list contains dictionaries
            representing recitation sections for a course.
            lectures (list): A list of lists, where each inner list contains dictionaries
            representing lecture sections for a course.

        Returns:
            list: A list of strings representing the updated schedule
            with recitation sections added.

        """
        newschedule = schedule
        for course in recs:
            if course != []:
                course_name = "-".join(course[0]["id"].split("-")[0:2])
                schedule_names = list(map(lambda x: "-".join(x[0].split("-")[0:2]), schedule))
                if course_name in schedule_names:
                    for section in course:
                        if check_if_schedule_possible(
                            schedule + [(section["id"], section["credits"])],
                            recs + lectures,
                            breaks,
                        ):
                            newschedule.append((section["id"], section["credits"]))
                            break
        return newschedule

    c_to_s = find_sections(courses)
    lectures = find_activities(c_to_s, "LEC")
    recs = find_activities(c_to_s, "REC")

    monday_schedules = scheduler_for_day(lectures, "M", breaks)
    tues_schedules = scheduler_for_day(lectures, "T", breaks)
    wed_schedules = scheduler_for_day(lectures, "W", breaks)
    thurs_schedules = scheduler_for_day(lectures, "R", breaks)
    fri_schedules = scheduler_for_day(lectures, "F", breaks)
    possible_mwf = []
    for i in range(len(monday_schedules)):
        for j in range(len(wed_schedules)):
            for k in range(len(fri_schedules)):
                possible_mwf.append(monday_schedules[i] + wed_schedules[j] + fri_schedules[k])

    possible_tr = []
    for i in range(len(tues_schedules)):
        for j in range(len(thurs_schedules)):
            possible_tr.append(tues_schedules[i] + thurs_schedules[j])

    total_schedules = []
    for i in range(len(possible_tr)):
        for j in range(len(possible_mwf)):
            total_schedules.append(possible_tr[i] + possible_mwf[j])
    courses = list(map(schedule_to_section, total_schedules))
    courses_unique = list(map(remove_duplicates, courses))

    choose = list(map(choose_class_hash, courses_unique))
    choose = [
        schedule for schedule in choose if check_if_schedule_possible(schedule, lectures, breaks)
    ]
    if count is not None:
        combinations = []
        for i in range(len(choose)):
            if len(choose[i]) <= count:
                combinations.append(choose[i])
            else:
                [
                    combinations.append(list(c))
                    for c in itertools.combinations(choose[i], int(count))
                    if c not in combinations
                ]
                [
                    combinations.append(list(c))
                    for c in itertools.combinations(choose[i], int(count) + 1)
                    if c not in combinations
                ]
    else:
        combinations = choose
    choose = [add_recs_to_schedule(schedule, recs, lectures, breaks) for schedule in combinations]
    choose = [schedule for schedule in choose if credit_count(schedule) <= count]
    choose = sorted(choose, key=lambda x: random.random())
    return choose