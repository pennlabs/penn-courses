import json
import os
import re

import requests
from django.conf import settings

from courses.models import Instructor
from courses.util import get_or_create_course_and_section
from review.models import Review


token = settings.PCR_TOKEN
base_url = 'https://api.penncoursereview.com/v1'


def extract_reviews(data, department):
    bit_re = re.compile(r'(^r)?([A-Z])')

    # For example, transform 'rCourseQuality' -> 'course_quality'.
    def pythonify_field(s): return bit_re.sub(r'_\2', s).lower()[1:]

    result = []
    for rev in data['values']:
        result.append({
            'instructor': rev['instructor']['name'],
            'section': [sec for sec in rev['section']['aliases'] if sec.startswith(department)][0],
            'semester': rev['section']['semester'],
            'ratings': dict([(pythonify_field(k), v) for k, v in rev['ratings'].items()])
        })
    return result


def save_reviews(revs, print_every=20):
    total = len(revs)
    i = 0
    for rev in revs:
        if Instructor.objects.filter(name__icontains=rev['instructor']).exists():
            instr = Instructor.objects.get(name__icontains=rev['instructor'])
        else:
            instr = Instructor.objects.create(name=rev['instructor'].title())
        _, sec = get_or_create_course_and_section(rev['section'], rev['semester'])
        sec.instructors.add(instr)
        review, _ = Review.objects.get_or_create(instructor=instr,
                                                 section=sec)
        review.set_scores(rev['ratings'])
        i += 1
        if print_every > 0 and i % print_every == 0:
            print(f'{i} / {total} reviews processed.')


def get_depts():
    r = requests.get(base_url + '/depts/', {'token': token})
    if r.status_code == 200:
        return [d['id'] for d in r.json()['result']['values']]

    return []


def get_reviews_for_department(dept):
    r = requests.get(base_url + f'/depts/{dept}/reviews/', {'token': token})
    if r.status_code == 200:
        return extract_reviews(r.json()['result'], dept)
    else:
        print(r.text)


def save_reviews_for_department(dept, filename):
    dept_reviews = get_reviews_for_department(dept)
    with open(filename, 'w') as f:
        json.dump(dept_reviews, f)


def load_reviews_for_department(filename):
    with open(filename) as f:
        save_reviews(json.load(f))


def save_all_reviews(directory):
    depts = get_depts()
    i = 0
    for dept in depts:
        i += 1
        print(f'loading {dept} reviews... ({i} / {len(depts)})')
        save_reviews_for_department(dept, os.path.join(directory, f'{dept}.json'))


def load_all_reviews(directory):
    reviews = []
    i = 0
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name.endswith('.json'):
                i += 1
                print(f'loading reviews from {name}... ({i} / {len(files)})')
                full_path = os.path.join(directory, name)
                with open(full_path) as f:
                    reviews.extend(json.load(f))
    save_reviews(reviews)
