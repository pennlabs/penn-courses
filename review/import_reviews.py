import json
import re

from courses.models import Instructor
from .models import Review
from courses.util import get_course_and_section


def load_data(fname='review/cis-reviews-test.json'):
    with open(fname) as f:
        return json.loads(f.read())


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


def save_reviews(revs):
    for rev in revs:
        instr, _ = Instructor.objects.get_or_create(name__contains=rev['instructor'],
                                                    defaults={'name': rev['instructor'].title()})
        _, sec = get_course_and_section(rev['section'], rev['semester'])
        sec.instructors.add(instr)
        review, _ = Review.objects.get_or_create(instructor=instr,
                                                 section=sec)
        review.set_scores(rev['ratings'])


def load_reviews():
    response = load_data()
    r = extract_reviews(response['result'], 'CIS')
    save_reviews(r)
