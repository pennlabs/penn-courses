from django.core.management.base import BaseCommand

from degree.data.premed import load


class Command(BaseCommand):
    help = "Create or update the pre-med major and its requirements (see degree/data/premed.py)."

    def handle(self, *args, **options):
        major = load()
        self.stdout.write(f"Loaded {major.name} ({major.program_code}, {major.year}).")
