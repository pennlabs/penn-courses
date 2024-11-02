from django.conf import settings
from django.core.management import BaseCommand
from django.db.models import Count

from plan.models import Schedule, NumberCalenders
from courses.models import Section
from courses.util import get_current_semester

class Command(BaseCommand):
    help = (
        '''This command will recompute, for each section, the number of PCP schedules (grouped by person)
        that this section is in.'''
    )

    def handle(self, *args, **options):
        current_semester = get_current_semester()

        # Get all sections for the current semester
        sections = Section.objects.filter(course__semester=current_semester)

        # Annotate each section with the count of unique users who have that section in any schedule
        sections_with_counts = sections.annotate(
            person_count=Count('schedule__person', distinct=True)
        )

        # Iterate over the sections and update or create NumberCalenders instances
        for section in sections_with_counts:
            count = section.person_count
            NumberCalenders.objects.update_or_create(
                section=section,
                semester=current_semester,
                defaults={'count': count}
            )

        self.stdout.write(self.style.SUCCESS('Successfully updated NumberCalenders for all sections.'))
