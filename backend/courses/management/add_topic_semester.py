from textwrap import dedent
from collections import Counter

from django.core.management.base import BaseCommand
from django.db.models.functions import Substr
from django.db import transaction
from tqdm import tqdm

from courses.models import Course, Topic
from courses.util import get_semesters
from review.management.commands.clearcache import clear_cache

def add_most_common_semester_topic(verbose=False):
    if verbose:
        print("Finding most common semester for topic groups...")
    
    for topic in tqdm(Topic.objects.all()):
        courses = Course.objects.filter(topic=topic, semester__isnull=False).values('semester').annotate(semester_char=Substr('semester', -1))

        semester_counts = Counter({course['semester']: 1 for course in courses})
        most_frequent_semester, _ = semester_counts.most_common(1)[0]

        topic.most_frequent_semester = most_frequent_semester
        topic.save()