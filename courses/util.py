import re
import json

from .models import *


def separate_course_code(course_code):
    """return (dept, course, section) ID tuple given a course code in any possible format"""
    course_regexes = [
        re.compile(r'([A-Za-z]+) *(\d{3})(\d{3})'),
        re.compile(r'([A-Za-z]+) *-(\d{3})-(\d{3})'),
    ]

    course_code = course_code.replace(' ', '').upper()
    for regex in course_regexes:
        m = regex.match(course_code)
        if m is not None:
            return m.group(1), m.group(2), m.group(3)

    raise ValueError(f'Course code could not be parsed: {course_code}')


def get_course_and_section(course_code, semester):
    dept_code, course_id, section_id = separate_course_code(course_code)

    dept, _ = Department.objects.get_or_create(code=dept_code)

    course, _ = Course.objects.get_or_create(department=dept,
                                             code=course_id,
                                             semester=semester)

    section, _ = Section.objects.get_or_create(course=course, code=section_id)

    return course, section


def record_update(section_id, semester, old_status, new_status, alerted, req):
    _, section = get_course_and_section(section_id, semester)
    u = StatusUpdate(section=section,
                     old_status=old_status,
                     new_status=new_status,
                     alert_sent=alerted,
                     request_body=req)
    u.save()
    return u


def add_instructors(section, names):
    for instructor in names:
        i, _ = Instructor.objects.get_or_create(name=instructor)
        section.instructors.add(i)
    section.save()


def get_room(building_code, room_number):
    building, _ = Building.objects.get_or_create(code=building_code)
    room, _ = Room.objects.get_or_create(building=building,
                                         number=room_number)
    return room


def add_meetings(section, meetings):
    for meeting in meetings:
        room = get_room(meeting['building_code'], meeting['room_number'])
        start_time = meeting['start_time_24'] * 100
        end_time = meeting['end_time_24'] * 100
        for day in list(meeting['meeting_days']):
            m, _ = Meeting.objects.get_or_create(section=section,
                                                 day=day,
                                                 start=start_time,
                                                 end=end_time,
                                                 room=room)


def add_associated_sections(section, info):
    semester = section.course.semester
    associations = ['labs', 'lectures', 'recitations']
    for assoc in associations:
        sections = info.get(assoc, [])
        for sect in sections:
            section_code = f"{sect['subject']}-{sect['course_id']}-{sect['section_id']}"
            _, associated = get_course_and_section(section_code, semester)
            section.associated_sections.add(associated)


def set_crosslistings(course, crosslist_primary):
    if len(crosslist_primary) == 0:
        course.primary_listing = course
    else:
        primary_course, _ = get_course_and_section(crosslist_primary, course.semester)
        course.primary_listing = primary_course


def add_restrictions(section, requirements):
    for r in requirements:
        rest, _ = Restriction.objects.get_or_create(code=r['registration_control_code'],
                                                    defaults={
                                                     'description': r['requirement_description']
                                                    })
        section.restrictions.add(rest)


def upsert_course_from_opendata(info, semester):
    course_code = info['section_id_normalized']
    course, section = get_course_and_section(course_code, semester)

    # https://stackoverflow.com/questions/11159118/incorrect-string-value-xef-xbf-xbd-for-column
    course.title = info['course_title'].replace('\uFFFD', '')
    course.description = info['course_description'].replace('\uFFFD', '')
    set_crosslistings(course, info['crosslist_primary'])

    try:
        section.credits = int(info['credits'].split(' ')[0])
    except:
        section.credits = 0

    section.status = info['course_status']
    section.capacity = int(info['max_enrollment'])
    section.activity = info['activity']
    section.prereq_notes = '\n'.join(info['prerequisite_notes'])
    section.meeting_times = json.dumps([meeting['meeting_days'] + ' '
                                        + meeting['start_time'] + ' - '
                                        + meeting['end_time'] for meeting in info['meetings']])

    add_instructors(section, [instructor['name'] for instructor in info['instructors']])
    add_meetings(section, info['meetings'])
    add_associated_sections(section, info)
    add_restrictions(section, info['requirements'])

    section.save()
    course.save()


def update_course_from_record(update):
    section = update.section
    section.status = update.new_status
    section.save()
