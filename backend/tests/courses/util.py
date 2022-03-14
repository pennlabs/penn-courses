from courses.models import Instructor
from courses.util import get_or_create_course_and_section, set_meetings
from review.models import Review


def create_mock_data(code, semester, meeting_days="MWF", start=11.0, end=12.0):
    course, section, _, _ = get_or_create_course_and_section(code, semester)
    course.description = "This is a fake class."
    course.save()
    section.credits = 1
    section.status = "O"
    section.activity = "LEC"
    section.save()
    m = [
        {
            "building_code": "LLAB",
            "room_number": "10",
            "meeting_days": meeting_days,
            "start_time_24": start,
            "end_time_24": end,
        }
    ]
    set_meetings(section, m)
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
