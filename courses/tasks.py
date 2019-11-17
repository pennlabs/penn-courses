import csv
import logging

from celery import shared_task

from django.utils.timezone import make_aware

import pytz

from courses import registrar
from courses.models import Course, Department, Requirement, Section, StatusUpdate
from courses.util import upsert_course_from_opendata
from options.models import get_value

from datetime import datetime


logger = logging.getLogger(__name__)


@shared_task(name='courses.tasks.load_courses')
def load_courses(query='', semester=None):
    if semester is None:
        semester = get_value('SEMESTER')

    logger.setLevel(logging.DEBUG)
    print('load in courses with prefix %s from %s' % (query, semester))
    results = registrar.get_courses(query, semester)

    num_courses = len(results)
    i = 0
    for course in results:
        if i % 100 == 0:
            print(f'loading in course {i} / {num_courses}')
        upsert_course_from_opendata(course, semester)
        i += 1

    return {'result': 'succeeded', 'name': 'courses.tasks.load_courses'}


def load_requirements(school=None, semester=None, requirements=None):
    """
    :param school: School to load requirements from. Current options are WH (Wharton) and SEAS (Engineering)
    :param semester: Semester to load requirements in for.
    :param requirements: If school is not specified, can input a custom requirements dict in this format:
    {
        codes: {"<requirement code>": "<full requirement name>", ...},
        data: [
            {
                "department": <department>,
                "course_id": <course id OR None if requirement is for whole course>},
                "satisfies": <False if describing a course override, True for courses and depts which satisfy the req>
            },
            ... [one dict for every requirement rule]
        ]
    }
    """
    if semester is None:
        semester = get_value('SEMESTER')

    if school == 'WH':
        from .requirements import wharton
        requirements = wharton.get_requirements()
    elif school == 'SEAS':
        from .requirements import engineering
        requirements = engineering.get_requirements()
    elif requirements is None:
        return None

    codes = requirements['codes']
    data = requirements['data']

    for req_id, items in data.items():
        # if this isn't a requirement we define in codes, then don't update it.
        if req_id not in codes:
            continue
        requirement = Requirement.objects.get_or_create(semester=semester,
                                                        school=school,
                                                        code=req_id,
                                                        defaults={
                                                          'name': codes[req_id]
                                                        })[0]
        for item in items:
            dept_id = item.get('department')
            course_id = item.get('course_id')
            satisfies = item.get('satisfies')
            dept, _ = Department.objects.get_or_create(code=dept_id)
            if course_id is None:
                requirement.departments.add(dept)
            else:
                # Unlike most functionality with courses, we do not want to create a relation between a course
                # and a requirement if the course does not exist.
                try:
                    course = Course.objects.get(department=dept, code=course_id, semester=semester)
                except Course.DoesNotExist:
                    continue
                if satisfies:
                    requirement.courses.add(course)
                else:
                    requirement.overrides.add(course)


@shared_task(name='courses.tasks.semester_sync')
def semester_sync(query='', semester=None):
    load_courses(query=query, semester=semester)
    load_requirements(school='SEAS', semester=semester)
    load_requirements(school='WH', semester=semester)


def load_course_status_history(full_path):
    row_count = 0
    with open(full_path, newline='') as history_file:
        history_reader = csv.reader(history_file, delimiter=',', quotechar='|')
        row_count = sum(1 for row in history_reader)
    with open(full_path, newline='') as history_file:
        print(f'beginning to load status history from {full_path}')
        history_reader = csv.reader(history_file, delimiter=',', quotechar='|')
        i = 1
        iter_reader = iter(history_reader)
        next(iter_reader)
        for row in iter_reader:
            i += 1
            if i % 100 == 1:
                print(f'loading status history... ({i} / {row_count})')
            section_code = row[4]+'-'+row[5]+'-'+row[6]
            row[3] += ' UTC'
            row[3] = datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S.%f %Z')
            row[3] = make_aware(row[3], timezone=pytz.utc, is_dst=None)
            if Section.objects.filter(full_code=section_code, course__semester=get_value('SEMESTER', None)).exists():
                sec = Section.objects.get(full_code=(row[4]+'-'+row[5]+'-'+row[6]),
                                          course__semester=get_value('SEMESTER', None))
                if StatusUpdate.objects.filter(section=sec).exists(): #this should not overwrite... it should clear all objects and then rewrite
                    status_update = StatusUpdate.objects.get(section=sec)
                    status_update.old_status = row[0]
                    status_update.new_status = row[1]
                    status_update.alert_sent = row[2]
                    status_update.created_at = row[3] # this does not work
                    status_update.save()
                else:
                    status_update = StatusUpdate(section=sec, old_status=row[0], new_status=row[1],
                                                 alert_sent=row[2], created_at=row[3])
                    status_update.save()
    print(f'finished loading status history from {full_path}... processed {row_count} rows')
