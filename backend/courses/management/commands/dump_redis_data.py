from courses.models import Course, Topic
from django.core.management.base import BaseCommand
from review.management.commands.clearcache import clear_cache


class Command(BaseCommand):

    help = """Load in the courses' metadata into Redis for full-text searching"""

    def handle(self, *args, **kwargs):
        pass
