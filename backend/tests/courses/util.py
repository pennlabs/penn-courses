from courses.management.commands.recompute_parent_courses import recompute_parent_courses
from courses.management.commands.recompute_soft_state import (
    recompute_precomputed_fields,
    recompute_topics,
)
from courses.models import Instructor
from courses.util import all_semesters, get_or_create_course_and_section, set_meetings
from review.models import Review


def time_str(time):
    return f"{time // 100:2d}:{int(time % 100):02d} {'AM' if time < 1200 else 'PM'}"


def fill_course_soft_state():
    semesters = all_semesters()
    recompute_precomputed_fields(verbose=False)
    recompute_parent_courses(semesters=semesters, skip_xwalk=True, verbose=False)
    recompute_topics(min_semester=min(semesters), verbose=False)


def create_mock_data(code, semester, meeting_days="MWF", start=1100, end=1200):
    course, section, _, _ = get_or_create_course_and_section(code, semester)
    course.description = "This is a fake class."
    course.save()
    section.credits = 1
    section.status = "O"
    section.activity = "LEC"
    section.save()
    section.crn = section.id
    section.save()
    m = [
        {
            "building_code": "LLAB",
            "room_code": "10",
            "days": meeting_days,
            "begin_time_24": start,
            "begin_time": time_str(start),
            "end_time_24": end,
            "end_time": time_str(end),
        }
    ]
    set_meetings(section, m)
    fill_course_soft_state()
    return course, section


def create_mock_data_with_reviews(code, semester, number_of_instructors):
    course, section = create_mock_data(code, semester)
    reviews = []
    for i in range(1, number_of_instructors + 1):
        instr, _ = Instructor.objects.get_or_create(name="Instructor" + str(i))
        section.instructors.add(instr)
        review = Review(section=section, instructor=instr, responses=100)
        review.save()
        review.set_averages(
            {
                "course_quality": 4 / i,
                "instructor_quality": 4 / (i + 1),
                "difficulty": 4 / (i + 2),
                "work_required": 4 / (i + 3),
            }
        )
        reviews.append(review)
    return course, section, reviews


def create_mock_async_class(code, semester):
    course, section = create_mock_data(code, semester)
    set_meetings(section, [])
    return course, section
