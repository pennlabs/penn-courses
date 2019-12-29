import csv
import os
from datetime import datetime

import pytz
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware

from courses.models import Section, StatusUpdate
from options.models import get_value


class Command(BaseCommand):
    help = 'Load course status history from CSV file into the database.'

    def add_arguments(self, parser):
        parser.add_argument('--src', nargs='?', type=str, default='')

    def handle(self, *args, **kwargs):
        src = os.path.abspath(kwargs['src'])
        _, file_extension = os.path.splitext(kwargs['src'])
        if not os.path.exists(src):
            return 'File does not exist.'
        if file_extension != '.csv':
            return 'File is not a csv.'
        with open(src, newline='') as history_file:
            history_reader = csv.reader(history_file, delimiter=',', quotechar='|')
            row_count = sum(1 for row in history_reader)
        with open(src, newline='') as history_file:
            print(f'beginning to load status history from {src}')
            history_reader = csv.reader(history_file, delimiter=',', quotechar='|')
            i = 1
            iter_reader = iter(history_reader)
            next(iter_reader)
            for row in iter_reader:
                i += 1
                if i % 100 == 1:
                    print(f'loading status history... ({i} / {row_count})')
                section_code = row[4] + '-' + row[5] + '-' + row[6]
                row[3] += ' UTC'
                row[3] = datetime.strptime(row[3], '%Y-%m-%d %H:%M:%S.%f %Z')
                row[3] = make_aware(row[3], timezone=pytz.utc, is_dst=None)
                if row[0] != 'O' and row[0] != 'C' and row[0] != 'X':
                    row[0] = ''
                if Section.objects.filter(full_code=section_code,
                                          course__semester=get_value('SEMESTER', None)).exists():
                    sec = Section.objects.get(full_code=(row[4] + '-' + row[5] + '-' + row[6]),
                                              course__semester=get_value('SEMESTER', None))
                    if not StatusUpdate.objects.filter(section=sec, old_status=row[0], new_status=row[1],
                                                       alert_sent=row[2], created_at=row[3]).exists():
                        status_update = StatusUpdate(section=sec, old_status=row[0], new_status=row[1],
                                                     alert_sent=row[2], created_at=row[3])
                        status_update.save()
        print(f'finished loading status history from {src}... processed {row_count} rows')
