import os
import subprocess
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Load course_documents from a pg_dump .dump archive (data-only) into the DB."

    def add_arguments(self, parser):
        parser.add_argument("dump_path", type=str)
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **opts):
        dump_path = Path(opts["dump_path"]).expanduser().resolve()
        force = opts["force"]

        if not dump_path.exists():
            raise CommandError(f"File not found: {dump_path}")

        with connection.cursor() as c:
            c.execute("SELECT to_regclass('public.course_documents')")
            if c.fetchone()[0] is None:
                raise CommandError("course_documents table missing. Run migrations first.")

            c.execute("SELECT COUNT(*) FROM course_documents")
            (count,) = c.fetchone()

            if count > 0 and not force:
                raise CommandError(
                    f"course_documents already has {count} rows. Re-run with --force to overwrite."
                )

            # wipe existing rows so restore is idempotent for teammates
            c.execute("TRUNCATE TABLE course_documents;")

        db = connection.settings_dict
        env = os.environ.copy()
        if db.get("PASSWORD"):
            env["PGPASSWORD"] = db["PASSWORD"]

        cmd = ["pg_restore", "--data-only", "--no-owner", "--no-privileges", "-d", db["NAME"]]
        if db.get("HOST"):
            cmd += ["-h", db["HOST"]]
        if db.get("PORT"):
            cmd += ["-p", str(db["PORT"])]
        if db.get("USER"):
            cmd += ["-U", db["USER"]]
        cmd += [str(dump_path)]

        self.stdout.write("Running: " + " ".join(cmd))
        subprocess.run(cmd, check=True, env=env)

        with connection.cursor() as c:
            c.execute("SELECT COUNT(*) FROM course_documents")
            (new_count,) = c.fetchone()

        self.stdout.write(self.style.SUCCESS(f"Imported {new_count} rows into course_documents."))
