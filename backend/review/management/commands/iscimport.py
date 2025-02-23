import gc
import io
import logging
import os
import zipfile

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from courses.management.commands.recompute_soft_state import recompute_has_reviews
from courses.util import get_current_semester
from PennCourses.settings.base import S3_client
from review.import_utils.import_to_db import (
    import_description_rows,
    import_ratings_rows,
    import_summary_rows,
)
from review.import_utils.parse_sql import load_sql_dump
from review.management.commands.clearcache import clear_cache
from review.management.commands.precompute_pcr_views import precompute_pcr_views
from review.models import Review


ISC_SUMMARY_TABLE = "TEST_PCR_SUMMARY_V"
ISC_SUMMARY_HIST_TABLE = "TEST_PCR_SUMMARY_HIST_V"
ISC_RATING_TABLE = "TEST_PCR_RATING_V"
ISC_CROSSLIST_TABLE = "TEST_PCR_CROSSLIST_SUMMARY_V"
ISC_DESC_TABLE = "TEST_PCR_COURSE_DESC_V"


def assert_semesters_not_current(semesters):
    current_semester = get_current_semester()
    for semester in semesters:
        if semester == current_semester:
            raise ValueError(
                f"You cannot import reviews for the current semester ({current_semester}). "
                f"Did you forget to update the SEMESTER option in the Django admin console?"
            )


class Command(BaseCommand):
    help = """
    Import course review data from the zip of mysqldump files that we get from ISC every semester.
    """

    def add_arguments(self, parser):
        parser.add_argument("src", help="path to directory or zip file holding .sql dumps.")

        file_options = parser.add_mutually_exclusive_group()
        file_options.add_argument(
            "-z",
            "--zip",
            action="store_true",
            help="extract from local zip file rather than directory.",
        )
        file_options.add_argument(
            "-s3", "--s3_bucket", help="download zip file from specified s3 bucket."
        )

        semesters = parser.add_mutually_exclusive_group()
        semesters.add_argument(
            "-s",
            "--semester",
            action="append",
            help="Semester to import in the `<year>[A|B|C]` format. Add as many as you like",
        )
        semesters.add_argument(
            "-a",
            "--all",
            action="store_true",
            dest="import_all",
            help="Import reviews from all semesters in the dump files.",
        )

        summary = parser.add_mutually_exclusive_group()
        summary.add_argument(
            "-c",
            "--current",
            dest="summary_file",
            action="store_const",
            const=ISC_SUMMARY_TABLE,
            help="""
            Use the SUMMARY file containing only data for the current semester.
            Smaller file size means faster runtime, but only has useful data from the past semester.
            """,
        )
        summary.add_argument(
            "-hst",
            "--historical",
            dest="summary_file",
            action="store_const",
            const=ISC_SUMMARY_HIST_TABLE,
            help="Use the larger SUMMARY_HIST file for backfilling the database.",
        )

        parser.add_argument(
            "--import-details",
            action="store_true",
            help="import reviewbit details from the large RATING table.",
        )
        parser.add_argument(
            "--import-extra-crosslistings",
            action="store_true",
            help="import crosslistings from supplemental CROSSLIST table.",
        )
        parser.add_argument(
            "--import-descriptions",
            action="store_true",
            help="import course descriptions from the DESCRIPTIONS table.",
        )

        parser.add_argument(
            "--no-progress-bar",
            action="store_false",
            dest="show_progress_bar",
            help="Show dynamic progress bars during execution",
        )

        parser.add_argument(
            "--force", action="store_true", help="Complete action in non-interactive mode."
        )

        parser.set_defaults(summary_file=ISC_SUMMARY_TABLE)

    def get_files(self, src, is_zipfile, tables_to_get):
        """
        Get file objects for the given tables at the root defined in `src.`
        Works for flat directories and zip files as well.

        Note that we are not being good POSIX citizens -- file objects are not closed
        """
        files = []
        self.zfile = None
        if is_zipfile:
            self.zfile = zipfile.ZipFile(src)
            for name in tables_to_get:
                zf = self.zfile.open(name + ".sql")
                files.append(io.TextIOWrapper(zf, "latin-1"))
        else:
            for name in tables_to_get:
                path = os.path.abspath(os.path.join(src, name + ".sql"))
                files.append(open(path, "r", encoding="latin-1"))
        return tuple(files)

    def close_files(self, files):
        for f in files:
            f.close()
        if self.zfile is not None:
            self.zfile.close()
            self.zfile = None

    def display(self, s):
        print(s, file=self.stdout)

    def handle(self, *args, **kwargs):
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)

        src = kwargs["src"]
        semesters = kwargs["semester"]
        import_all = kwargs["import_all"]
        s3_bucket = kwargs["s3_bucket"]
        is_zip_file = kwargs["zip"] or s3_bucket is not None
        summary_file = kwargs["summary_file"]  # either summary table or summary hist table
        import_details = kwargs["import_details"]
        import_descriptions = kwargs["import_descriptions"]
        show_progress_bar = kwargs["show_progress_bar"]
        force = kwargs["force"]

        if src is None:
            raise CommandError("source directory or zip must be defined.")

        if semesters is None and not import_all:
            raise CommandError(
                "Must define semester with (-s) or explicitly import all semesters with (-a)."
            )
        if semesters is not None:
            assert_semesters_not_current(semesters)

        if s3_bucket is not None:
            fp = "/tmp/pcrdump.zip"
            # Make sure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
            # are loaded in as environment variables.
            print(f"downloading zip from s3 bucket: {src}")
            S3_client.download_file(s3_bucket, src, fp)
            src = fp

        print(
            "This script is an atomic transaction, meaning the database will only be "
            "modified if the whole script succeeds."
        )

        tables_to_get = [summary_file]
        idx = 1
        detail_idx = -1
        if import_details:
            tables_to_get.append(ISC_RATING_TABLE)
            detail_idx = idx
            idx += 1

        description_idx = -1
        if import_descriptions:
            tables_to_get.append(ISC_DESC_TABLE)
            description_idx = idx
            idx += 1

        files = self.get_files(src, is_zip_file, tables_to_get)
        summary_fo = files[0]

        print("Loading summary file...")
        summary_rows = load_sql_dump(summary_fo, progress=show_progress_bar, lazy=False)
        gc.collect()
        print("SQL parsed and loaded!")
        if not import_all:
            full_len = len(summary_rows)
            summary_rows = [r for r in summary_rows if r["TERM"] in semesters]
            gc.collect()
            filtered_len = len(summary_rows)
            print(f"Filtered {full_len} rows down to {filtered_len} rows.")
        semesters = sorted(list({r["TERM"] for r in summary_rows}))
        gc.collect()

        for semester in semesters:
            print(f"Loading {semester}...")
            with transaction.atomic():  # Commit changes if all imports for the semester succeed
                to_delete = Review.objects.filter(section__course__semester=semester)
                delete_count = to_delete.count()
                if delete_count > 0:
                    if not force:
                        prompt = input(
                            f"This import will overwrite {delete_count} rows that have already been"
                            + "imported. Continue? (y/N) "
                        )
                        if prompt.strip().upper() != "Y":
                            print("Aborting...")
                            return 0

                    print(
                        f"Deleting {delete_count} existing reviews for {semester} "
                        "from the database..."
                    )
                    to_delete.delete()

                print(f"Importing reviews for semester {semester}")
                stats = import_summary_rows(
                    (r for r in summary_rows if r["TERM"] == semester), show_progress_bar
                )
                print(stats)

                gc.collect()

        with transaction.atomic():
            if import_details:
                print("Loading details file...")
                stats = import_ratings_rows(
                    *load_sql_dump(files[detail_idx]), semesters, show_progress_bar
                )
                print(stats)

            gc.collect()

            if import_descriptions:
                print("Loading descriptions file...")
                stats = import_description_rows(
                    *load_sql_dump(files[description_idx]),
                    None if import_all else semesters,
                    show_progress_bar,
                )
                print(stats)

        self.close_files(files)
        # invalidate cached views
        print("Invalidating cache...")
        del_count = clear_cache()
        print(f"{del_count if del_count >=0 else 'all'} cache entries removed.")

        gc.collect()

        print("Recomputing Section.has_reviews...")
        recompute_has_reviews()
        precompute_pcr_views(verbose=True, is_new_data=True)

        print("Done.")
        return 0
