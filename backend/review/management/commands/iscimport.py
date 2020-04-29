import io
import os
import zipfile

import boto3
from django.core.management.base import BaseCommand, CommandError

from review.import_utils.import_to_db import import_ratings_rows, import_summary_rows
from review.import_utils.parse_sql import load_sql_dump
from review.models import Review


ISC_SUMMARY_TABLE = "TEST_PCR_SUMMARY_V"
ISC_SUMMARY_HIST_TABLE = "TEST_PCR_SUMMARY_HIST_V"
ISC_RATING_TABLE = "TEST_PCR_RATING_V"
ISC_CROSSLIST_TABLE = "TEST_PCR_CROSSLIST_SUMMARY_V"
ISC_DESC_TABLE = "TEST_PCR_COURSE_DESC_V"


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
            "--no-progress-bar",
            action="store_false",
            dest="show_progress_bar",
            help="Show dynamic progress bars during execution",
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
        src = kwargs["src"]
        semesters = kwargs["semester"]
        import_all = kwargs["import_all"]
        s3_bucket = kwargs["s3_bucket"]
        is_zip_file = kwargs["zip"] or s3_bucket is not None
        summary_file = kwargs["summary_file"]
        import_details = kwargs["import_details"]
        show_progress_bar = kwargs["show_progress_bar"]

        if src is None:
            raise CommandError("source directory or zip must be defined.")

        if semesters is None and not kwargs["import_all"]:
            raise CommandError(
                "Must define semester with (-s) or explicitly import all semesters with (-a)."
            )

        if kwargs["s3_bucket"] is not None:
            fp = "/tmp/pcrdump.zip"
            # Make sure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
            # are loaded in as environment variables.
            boto3.client("s3").download_file(kwargs["s3_bucket"], src, fp)
            src = fp

        # TODO: When we import details and crosslistings, get their data here too.
        tables_to_get = [summary_file]
        if import_details:
            tables_to_get.append(ISC_RATING_TABLE)

        files = self.get_files(src, is_zip_file, tables_to_get)

        summary_fo = files[0]
        self.display(f"Loading summary file...")
        summary_rows = load_sql_dump(
            summary_fo, show_progress_bar
        )  # This will show a progress bar.
        self.display(f"SQL parsed and loaded!")

        if not import_all:
            full_len = len(summary_rows)
            summary_rows = [r for r in summary_rows if r["TERM"] in semesters]
            filtered_len = len(summary_rows)
            self.display(f"Filtered {full_len} rows down to {filtered_len} rows.")
            to_delete = Review.objects.filter(section__course__semester__in=semesters)
        else:
            to_delete = Review.objects.all()

        delete_count = to_delete.count()

        if delete_count > 0:
            prompt = input(
                f"This import will overwrite {delete_count} rows that have already been imported. Continue? (y/N) "  # noqa E501
            )
            if prompt.strip().upper() != "Y":
                self.display("Aborting...")
                return 0

            self.display(
                f"Deleting {delete_count} existing reviews for semesters from the database..."
            )
            to_delete.delete()

        self.display(
            f"Importing reviews for semester(s) {', '.join(semesters) if not kwargs['import_all'] else 'all'}"  # noqa E501
        )
        stats = import_summary_rows(summary_rows, show_progress_bar)
        self.display(stats)

        if import_details:
            self.display("Loading details file...")
            detail_rows = load_sql_dump(files[1], show_progress_bar)
            self.display("SQL parsed and loaded!")
            if not import_all:
                full_len = len(detail_rows)
                detail_rows = [r for r in detail_rows if r["TERM"] in semesters]
                filtered_len = len(detail_rows)
                self.display(f"Filtered {full_len} rows down to {filtered_len} rows.")
            stats = import_ratings_rows(detail_rows, show_progress_bar)
            self.display(stats)

        self.close_files(files)
        return 0
