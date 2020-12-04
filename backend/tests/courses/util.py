from courses.models import Instructor
from courses.util import get_or_create_course_and_section, set_meetings
from review.models import Review


def create_data_with_type(code, semester, type):
    course, section, _, _ = get_or_create_course_and_section(code, semester)
    section.credits = 1
    section.status = "O"
    section.activity = type
    section.save()
    course.sections.add(section)

def create_mock_data(code, semester):
    course, section, _, _ = get_or_create_course_and_section(code, semester)
    section.credits = 1
    section.status = "O"
    section.activity = "LEC"
    section.save()
    m = [
        {
            "building_code": "LLAB",
            "building_name": "Leidy Laboratories of Biology",
            "end_hour_24": 12,
            "end_minutes": 0,
            "end_time": "12:00 PM",
            "end_time_24": 12.0,
            "meeting_days": "MWF",
            "room_number": "10",
            "section_id": "CIS 120001",
            "section_id_normalized": "CIS -120-001",
            "start_hour_24": 11,
            "start_minutes": 0,
            "start_time": "11:00 AM",
            "start_time_24": 11.0,
            "term": "2019C",
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
        review = Review(section=section, instructor=instr)
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
