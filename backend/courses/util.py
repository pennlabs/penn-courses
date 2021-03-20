import json
import re

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
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
    Requirement,
    Restriction,
    Room,
    Section,
    StatusUpdate,
)
from review.util import titleize


def get_current_semester():
    """
    This function retrieves the string value of the current semester, either from
    memory (if the value has been cached), or from the db (after which it will cache
    the value for future use). If the value retrieved from the db is None, an error is thrown
    indicating that the SEMESTER Option must be set for this API to work properly.
    The cache has no timeout, but is invalidated whenever the SEMESTER Option is saved
    (which will occur whenever it is updated), using a post_save hook.
    See the invalidate_current_semester_cache function below to see how this works.
    """
    cached_val = cache.get("SEMESTER", None)
    if cached_val is not None:
        return cached_val
    retrieved_val = get_value("SEMESTER", None)
    if retrieved_val is None:
        raise APIException(
            "The SEMESTER runtime option is not set.  If you are in dev, you can set this "
            "option by running the command "
            "'python manage.py setoption SEMESTER 2020C', "
            "replacing 2020C with the current semester, in the backend directory (remember "
            "to run 'pipenv shell' before running this command, though)."
        )
    cache.set("SEMESTER", retrieved_val, timeout=None)  # cache only expires upon invalidation
    return retrieved_val


def get_semester(datetime):
    if 3 <= datetime.month and datetime.month <= 9:
        sem = str(datetime.year) + "C"
    else:
        if datetime.month < 3:
            sem = str(datetime.year) + "A"
        else:
            sem = str(datetime.year + 1) + "A"
    return sem


@receiver(post_save, sender=Option, dispatch_uid="invalidate_current_semester_cache")
def invalidate_current_semester_cache(sender, instance, **kwargs):
    """
    This function invalidates the cached SEMESTER value when the SEMESTER option is updated.
    Note that the timeout value on the cached SEMESTER value is set to None (meaning
    the cache will not be invalidated by any amount of elapsed time; saving the SEMESTER Option
    is the only way to invalidate this cached value).
    """
    if instance.key == "SEMESTER":
        cache.delete("SEMESTER")


def separate_course_code(course_code):
    """return (dept, course, section) ID tuple given a course code in any possible format"""
    course_regexes = [
        re.compile(r"([A-Za-z]+) *(\d{3}|[A-Z]{3})(\d{3})"),
        re.compile(r"([A-Za-z]+) *-(\d{3}|[A-Z]{3})-(\d{3})"),
    ]

    course_code = course_code.replace(" ", "").upper()
    for regex in course_regexes:
        m = regex.match(course_code)
        if m is not None:
            return m.group(1), m.group(2), m.group(3)

    raise ValueError(f"Course code could not be parsed: {course_code}")


def get_or_create_course(dept_code, course_id, semester):
    dept, _ = Department.objects.get_or_create(code=dept_code)
    course, c = Course.objects.get_or_create(department=dept, code=course_id, semester=semester)

    return course, c


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


def record_update(section_id, semester, old_status, new_status, alerted, req):
    _, section, _, _ = get_or_create_course_and_section(section_id, semester)
    u = StatusUpdate(
        section=section,
        old_status=old_status,
        new_status=new_status,
        alert_sent=alerted,
        request_body=req,
    )
    u.save()
    return u


def set_instructors(section, names):
    instructors = []
    for instructor in names:
        i, _ = Instructor.objects.get_or_create(name=instructor)
        instructors.append(i)
    section.instructors.set(instructors)


def get_room(building_code, room_number):
    building, _ = Building.objects.get_or_create(code=building_code)
    room, _ = Room.objects.get_or_create(building=building, number=room_number)
    return room


def set_meetings(section, meetings):
    section.meetings.all().delete()
    for meeting in meetings:
        room = get_room(meeting["building_code"], meeting["room_number"])
        start_time = meeting["start_time_24"]
        end_time = meeting["end_time_24"]
        for day in list(meeting["meeting_days"]):
            m, _ = Meeting.objects.update_or_create(
                section=section, day=day, start=start_time, end=end_time, defaults={"room": room}
            )


def add_associated_sections(section, info):
    semester = section.course.semester
    associations = ["labs", "lectures", "recitations"]
    for assoc in associations:
        sections = info.get(assoc, [])
        for sect in sections:
            section_code = f"{sect['subject']}-{sect['course_id']}-{sect['section_id']}"
            _, associated, _, _ = get_or_create_course_and_section(section_code, semester)
            section.associated_sections.add(associated)


def set_crosslistings(course, crosslist_primary):
    if len(crosslist_primary) == 0:
        course.primary_listing = course
    else:
        primary_course, _, _, _ = get_or_create_course_and_section(
            crosslist_primary, course.semester
        )
        course.primary_listing = primary_course


def add_restrictions(section, requirements):
    for r in requirements:
        rest, _ = Restriction.objects.get_or_create(
            code=r["registration_control_code"],
            defaults={"description": r["requirement_description"]},
        )
        section.restrictions.add(rest)


def add_college_requirements(course, college_reqs):
    code_to_name = {
        "MDS": "Society Sector",
        "MDH": "History & Tradition Sector",
        "MDA": "Arts & Letters Sector",
        "MDO": "Humanities & Social Science Sector",
        "MDL": "Living World Sector",
        "MDP": "Physical World Sector",
        "MDN": "Natural Science & Math Sector",
        "MWC": "Writing Requirement",
        "MQS": "College Quantitative Data Analysis Req.",
        "MFR": "Formal Reasoning Course",
        "MC1": "Cross Cultural Analysis",
        "MC2": "Cultural Diversity in the US",
        "MGH": "Benjamin Franklin Seminars",
    }
    name_to_code = dict([(v, k) for k, v in code_to_name.items()])
    for req_name in college_reqs:
        req = Requirement.objects.get_or_create(
            semester=course.semester,
            school="SAS",
            code=name_to_code[req_name],
            defaults={"name": req_name},
        )[0]
        req.courses.add(course)


def relocate_reqs_from_restrictions(rests, reqs, travellers):
    for t in travellers:
        if any(r["requirement_description"] == t for r in rests):
            reqs.append(t)


def upsert_course_from_opendata(info, semester):
    course_code = info["section_id_normalized"]
    try:
        course, section, _, _ = get_or_create_course_and_section(course_code, semester)
    except ValueError:
        return  # if we can't parse the course code, skip this course.

    # https://stackoverflow.com/questions/11159118/incorrect-string-value-xef-xbf-xbd-for-column
    course.title = info["course_title"].replace("\uFFFD", "")
    course.description = info["course_description"].replace("\uFFFD", "")
    course.prerequisites = "\n".join(info["prerequisite_notes"])
    set_crosslistings(course, info["crosslist_primary"])

    m = re.match(r"([0-9]*(\.[0-9]+)?) CU", info["credits"])
    if info["credit_type"] == "CU" and m is not None:
        try:
            section.credits = float(m.group(1))
        except ValueError:
            section.credits = 0
        except IndexError:
            section.credits = 0

    section.capacity = int(info["max_enrollment"])
    section.activity = info["activity"]
    section.meeting_times = json.dumps(
        [
            meeting["meeting_days"] + " " + meeting["start_time"] + " - " + meeting["end_time"]
            for meeting in info["meetings"]
        ]
    )

    set_instructors(section, [titleize(instructor["name"]) for instructor in info["instructors"]])
    set_meetings(section, info["meetings"])
    add_associated_sections(section, info)
    add_restrictions(section, info["requirements"])
    relocate_reqs_from_restrictions(
        info["requirements"],
        info["fulfills_college_requirements"],
        [
            "Humanities & Social Science Sector",
            "Natural Science & Math Sector",
            "Benjamin Franklin Seminars",
        ],
    )
    add_college_requirements(section.course, info["fulfills_college_requirements"])

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
