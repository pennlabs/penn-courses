import json
import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from alert.management.commands.recomputestats import recompute_stats
from courses.models import Meeting, Section


def parse_meeting_times_string(section: Section):
    meeting_times = json.loads(section.meeting_times)
    meetings = []
    for meeting_time in meeting_times:
        days, time_start, time_start_period, _, time_end, time_end_period = meeting_time.split()
        for day in days:
            assert day in "MTWRF"
            meeting = Meeting(
                section=section,
                start=convert_time(time_start, time_start_period),
                end=convert_time(time_end, time_end_period),
                day=day,
            )
            meetings.append(meeting)
    return meetings


def convert_time(time: str, time_period: str):
    hr, mins = time.split(":")
    offset = 12 if time_period.upper() == "PM" else 0
    return int(hr) + offset + int(mins) / 100


def delete_prompt(section: Section) -> bool:
    while True:
        inp = input(
            f"delete meetings {[str(meeting) for meeting in section.meetings.all()]}? [y/n]"
        )
        if inp == "y":
            return True
        elif inp == "n":
            return False


class Command(BaseCommand):
    help = "Create meetings from the meeting_times strings of sections"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Do not prompt when meetings already exist for a section",
        )

        parser.add_argument(
            "--fail_loud", action="store_true", help="Fail loudly if a meeting_times fails to parse"
        )

        parser.add_argument(
            "--dry_run", action="store_true", help="Dry run, without actually touching database"
        )

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        with transaction.atomic():
            for section in tqdm(Section.objects.all()):
                # delete existing meetings
                if not kwargs["dry_run"] and section.meetings.count() > 0:
                    should_delete = kwargs["force"] or delete_prompt(section)
                    if should_delete:
                        section.meetings.all().delete()
                    else:
                        print(f"skipping section {str(section)}")
                        continue

                # create new meetings
                try:
                    meetings = parse_meeting_times_string(section)
                except Exception:
                    if kwargs["fail_loud"]:
                        raise

                # save
                if kwargs["dry_run"]:
                    print([str(meeting) for meeting in meetings])
                    continue
                for meeting in meetings:
                    meeting.save()
        print("Running recompute_stats (to makes sure Section.num_meetings is set correctly)...")
        recompute_stats()
