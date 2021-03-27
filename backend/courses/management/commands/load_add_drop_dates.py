import logging
from datetime import datetime

import pytz
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import make_aware

from alert.models import AddDropPeriod, validate_add_drop_semester
from courses.util import get_current_semester
from PennCourses.settings.base import TIME_ZONE


def load_add_drop_dates(verbose=False):
    semester = get_current_semester()
    validate_add_drop_semester(semester)
    if verbose:
        print(f"Loading add/drop period dates for semester {semester} from the Almanac")
    with transaction.atomic():
        start_date, end_date = None, None
        try:
            previous = AddDropPeriod.objects.get(semester=semester)
            start_date = previous.start
            end_date = previous.end
            previous.delete()
        except AddDropPeriod.DoesNotExist:
            pass
        html = requests.get("https://almanac.upenn.edu/penn-academic-calendar").content
        soup = BeautifulSoup(html, "html.parser")
        if semester[4] == "C":
            start_sem = semester[:4] + " spring"
            end_sem = semester[:4] + " fall"
        elif semester[4] == "A":
            start_sem = str(int(semester[:4]) - 1) + " fall"
            end_sem = semester[:4] + " spring"
        else:
            raise ValueError(
                "This script currently only supports fall or spring semesters; "
                f"{semester} is invalid"
            )
        tz = pytz.timezone(TIME_ZONE)

        s_year, s_month, s_day, e_year, e_month, e_day = (None,) * 6
        start_mode = 0  # 0 if start semester hasn't been found, 1 if it has, 2 if finished sem
        end_mode = 0  # 0 if end semester hasn't been found, 1 if it has, 2 if finished sem
        all_th_parents = [el.parent for el in soup.find_all("th")]
        months = [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ]
        for tr_el in soup.find_all("tr"):
            if tr_el in all_th_parents:
                sem_name = tr_el.th.get_text().lower()
                if start_sem in sem_name:
                    start_mode = 1
                elif start_mode == 1:
                    start_mode = 2
                if end_sem in sem_name:
                    end_mode = 1
                elif end_mode == 1:
                    end_mode = 2
            else:
                children = list(tr_el.findChildren("td", recursive=False))
                title = children[0]
                date_string = children[1].get_text()
                if title is not None and "advance registration" in title.get_text().lower():
                    if start_mode == 1:
                        dates = date_string.split("-")
                        ar_begin_month = None
                        for month in months:
                            if month in dates[0].lower():
                                ar_begin_month = month
                        ar_end_month = None
                        for month in months:
                            if month in dates[0].lower():
                                ar_end_month = month
                        if ar_end_month is None:
                            ar_end_month = ar_begin_month
                        s_year = int(start_sem[:4])
                        if ar_end_month is not None:
                            s_month = months.index(ar_end_month) + 1
                        day_candidates = [int(s) for s in dates[1].split() if s.isdigit()]
                        if len(day_candidates) > 0:
                            s_day = day_candidates[0]
                if title is not None and "drop period ends" in title.get_text().lower():
                    if end_mode == 1:
                        drop_end_month = None
                        for month in months:
                            if month in date_string.lower():
                                drop_end_month = month
                        e_year = int(end_sem[:4])
                        if drop_end_month is not None:
                            e_month = months.index(drop_end_month) + 1
                        day_candidates = [int(s) for s in date_string.split() if s.isdigit()]
                        if len(day_candidates) > 0:
                            e_day = day_candidates[0]
        if all([d is not None for d in [s_year, s_month, s_day]]):
            start_date = make_aware(
                datetime.strptime(f"{s_year}-{s_month}-{s_day} 00:00", "%Y-%m-%d %H:%M"),
                timezone=tz,
            )
        if all([d is not None for d in [e_year, e_month, e_day]]):
            end_date = make_aware(
                datetime.strptime(f"{e_year}-{e_month}-{e_day} 00:00", "%Y-%m-%d %H:%M"),
                timezone=tz,
            )
        adp = AddDropPeriod(semester=semester, start=start_date, end=end_date)
        adp.save()
    if verbose:
        print("Done!")


class Command(BaseCommand):
    help = (
        "Load in the start and end date of the current semester's add drop period "
        "from the Penn Almanac."
    )

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        load_add_drop_dates(verbose=True)
