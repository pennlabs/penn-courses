import os

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Max, Min, OuterRef, Subquery, Value
from tqdm import tqdm

from courses.models import Course
from PennCourses.settings.base import FIRST_BANNER_SEM, XWALK_S3_BUCKET, XWALK_SRC, S3_client
from review.management.commands.clearcache import clear_cache


def get_crosswalk(cross_walk):
    """
    From a given crosswalk csv path, generate a dict mapping old_full_code to
    a list of the new codes originating from that source.
    """
    links = dict()
    cross_walk = pd.read_csv(cross_walk, delimiter="|", encoding="unicode_escape", dtype=str)
    for _, r in cross_walk.iterrows():
        old_full_code = f"{r['SRS_SUBJ_CODE']}-{r['SRS_COURSE_NUMBER']}"
        new_full_code = f"{r['NGSS_SUBJECT']}-{r['NGSS_COURSE_NUMBER']}"
        if old_full_code not in links:
            links[old_full_code] = []
        links[old_full_code].append(new_full_code)
    return links


def get_crosswalk_s3(verbose=False):
    """
    From the crosswalk crosswalk from settings/base.py, generate a dict mapping
    old_full_code to a list of the new codes originating from that source.
    """
    fp = "/tmp/" + XWALK_SRC
    if verbose:
        print(f"downloading crosswalk from s3://{XWALK_S3_BUCKET}/{XWALK_SRC}")
    S3_client.download_file(XWALK_S3_BUCKET, XWALK_SRC, fp)

    crosswalk = get_crosswalk(fp)

    # Remove temporary file
    os.remove(fp)

    return crosswalk


def load_crosswalk(print_missing=False, verbose=False):
    """
    Loads the crosswalk from settings/base.py, updating parent_course links.
    Returns the set of semesters of updated children.

    :param print_missing: If True, prints courses involved in crosswalk links that were
        not found in the database.
    :param verbose: A flag indicating whether this script should print its progress.
    """
    crosswalk = get_crosswalk_s3(verbose=verbose)
    root_course_codes = crosswalk.keys()
    child_course_codes = [c for children in crosswalk.values() for c in children]

    if verbose:
        print("Loading crosswalk.")

    num_changed_parent_links = 0
    num_missing_roots = 0
    num_missing_children = 0

    with transaction.atomic():
        root_courses = (
            Course.objects.filter(full_code__in=root_course_codes, semester__lt=FIRST_BANNER_SEM)
            .annotate(
                max_semester=Subquery(
                    Course.objects.filter(
                        full_code=OuterRef("full_code"), semester__lt=FIRST_BANNER_SEM
                    )
                    .annotate(common=Value(1))
                    .values("common")
                    .annotate(max_semester=Max("semester"))
                    .values("max_semester")
                )
            )
            .filter(semester=F("max_semester"))
            .annotate(department_code=F("department__code"))
        )
        root_courses = {r.full_code: r for r in root_courses}
        child_courses = (
            Course.objects.filter(full_code__in=child_course_codes, semester__gte=FIRST_BANNER_SEM)
            .annotate(
                min_semester=Subquery(
                    Course.objects.filter(
                        full_code=OuterRef("full_code"), semester__gte=FIRST_BANNER_SEM
                    )
                    .annotate(common=Value(1))
                    .values("common")
                    .annotate(min_semester=Min("semester"))
                    .values("min_semester")
                )
            )
            .filter(semester=F("min_semester"))
            .annotate(department_code=F("department__code"))
        )
        child_courses = {child.full_code: child for child in child_courses}
        for root_course_code, children_codes in tqdm(crosswalk.items(), disable=not verbose):
            if root_course_code not in root_courses:
                num_missing_roots += 1
                if print_missing:
                    print(f"Root course {root_course_code} before {FIRST_BANNER_SEM} not found.")
                continue
            root_course = root_courses[root_course_code]

            to_update = []
            for child_code in children_codes:
                if child_code not in child_courses:
                    num_missing_children += 1
                    if print_missing:
                        print(
                            f"Child course {child_code} in or after {FIRST_BANNER_SEM} not found."
                        )
                    continue
                child = child_courses[child_code]
                parent_course = root_course
                if child.department_code != root_course.department_code:
                    for xlist_parent in root_course.crosslistings.all():
                        if xlist_parent.full_code.startswith(f"{child.department_code}-"):
                            parent_course = xlist_parent
                if child.parent_course != parent_course:
                    child.parent_course = parent_course
                    to_update.append(child)
                    num_changed_parent_links += 1
            Course.objects.bulk_update(to_update, ["parent_course"])
        if verbose:
            print(f"Changed {num_changed_parent_links} parent_course links.")
            print(f"{num_missing_roots}/{len(crosswalk)} roots not found in db")
            print(
                f"{num_missing_children}/{sum(len(c) for c in crosswalk.values())} "
                "children not found in db"
            )


class Command(BaseCommand):
    help = "This script loads the crosswalk from settings/base.py, updating parent_course links."

    def add_arguments(self, parser):
        parser.add_argument(
            "--print-missing",
            action="store_true",
            help="Print out all missing roots and children.",
        )

    def handle(self, *args, **kwargs):
        load_crosswalk(print_missing=kwargs["print_missing"], verbose=True)

        print("Clearing cache")
        del_count = clear_cache()
        print(f"{del_count if del_count >=0 else 'all'} cache entries removed.")
