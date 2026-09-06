from collections import defaultdict
from dataclasses import dataclass, field
from textwrap import dedent

from django.core.management.base import BaseCommand
from django.db import transaction

from degree.management.commands.deduplicate_rules import deduplicate_rules
from degree.models import Degree, Major, Minor, program_code_to_name
from degree.utils.parse_path_audit import find_block, parse_audit, save_component, save_parsed_audit
from degree.utils.path_client import PathClient, split_program_code, split_program_title


# Students with degrees older than this catalog year are not supported, and their degrees are not stored in the database. 
EARLIEST_CATALOG_YEAR = 2022


@dataclass
class Tally:
    """Tracks the results of a run."""

    saved: int = 0
    skipped: int = 0
    outdated: int = 0
    majors: int = 0
    minors: int = 0
    failures: list[tuple[str, str]] = field(default_factory=list)

    def skip(self, code, reason, *, announce=True):
        self.skipped += 1
        if announce:
            print(f"Skipping {code}: {reason}")

    def fail(self, code, error):
        reason = f"{type(error).__name__}: {error}"
        self.failures.append((code, reason))
        self.skip(code, reason)

    def report(self):
        print(f"Saved {self.saved} degrees, skipped {self.skipped}")
        if self.outdated:
            print(f"  of those, {self.outdated} predate catalog year {EARLIEST_CATALOG_YEAR}")
        print(f"Saved {self.majors} majors and {self.minors} minors")

        if not self.failures:
            return

        by_reason = defaultdict(list)
        for code, reason in self.failures:
            by_reason[reason].append(code)

        print(f"\n{len(self.failures)} programs failed, by reason:")
        for reason, codes in sorted(by_reason.items(), key=lambda item: -len(item[1])):
            shown = ", ".join(codes[:8])
            if len(codes) > 8:
                shown += f", ... (+{len(codes) - 8} more)"
            print(f"  [{len(codes):3}] {reason}\n        {shown}")


class Command(BaseCommand):
    help = dedent(
        """
        Fetches, parses and stores degrees from Path@Penn.

        Note: this script deletes any existing degrees in the database that overlap with the
        degrees fetched from Path.
        """
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--srcdb",
            nargs="+",
            required=True,
            help=dedent(
                """
                One or more Path term codes to fetch, e.g. 202630. A term maps to a catalog
                year rather than being one (202630 serves the 2027 catalog), so the year each
                degree is stored under is read from the audit, not from this argument.
                """
            ),
        )
        parser.add_argument(
            "--program",
            nargs="+",
            help=dedent(
                """
                Only fetch these Path program codes, e.g. CMPE-BSE. Fetches every
                undergraduate program in the catalog if not given.
                """
            ),
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=0.5,
            help="Seconds to wait between requests to Path. Defaults to 0.5.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Fetch and parse, but do not write anything to the database.",
        )
        parser.add_argument(
            "--skip-minors",
            action="store_true",
            help=dedent(
                """
                Do not fetch minors. 
                """
            ),
        )
        parser.add_argument("--deduplicate-rules", action="store_true")

    def handle(self, *args, **options):
        self.options = options
        self.verbosity = options["verbosity"]
        self.dry_run = options["dry_run"]

        client = PathClient(delay=options["delay"])
        tally = Tally()

        for srcdb in options["srcdb"]:
            self.fetch_degrees(client, srcdb, tally)
            if not options["skip_minors"] and not options["program"]:
                self.fetch_minors(client, srcdb, tally)

        tally.report()

        if options["deduplicate_rules"] and not self.dry_run:
            self.announce("Deduplicating rules...")
            deduplicate_rules(verbose=self.verbosity)

    def announce(self, message, *, level=1):
        if self.verbosity >= level:
            print(message)

    def fetch_degrees(self, client, srcdb, tally):
        if self.options["program"]:
            programs = [{"code": code, "title": ""} for code in self.options["program"]]
        else:
            programs = client.undergraduate_programs(srcdb)
        self.announce(f"srcdb {srcdb}: {len(programs)} programs")

        for program in programs:
            self.fetch_degree(client, srcdb, program, tally)

    def fetch_degree(self, client, srcdb, program, tally):
        """
        Loads one program as a Degree, and its major as a Major for students who add it on top
        of a different degree.
        """
        code = program["code"]
        try:
            info = client.program_info(code, srcdb)
        except Exception as error:
            tally.fail(code, error)
            return

        sis_program = info.get("sis_prog_code")
        if sis_program not in program_code_to_name:
            reason = f"{sis_program} is not a program we model"
            tally.skip(code, reason, announce=False)
            self.announce(f"Skipping {code}: {reason}", level=2)
            return

        _, degree_code, concentration = split_program_code(code)
        major_name, concentration_name = split_program_title(
            program["title"] or info.get("prog_name") or "", degree_code
        )
        degree = Degree(
            program=sis_program,
            degree=info.get("degc_code") or degree_code,
            major=info.get("majr_code") or code.split("-")[0],
            major_name=major_name or None,
            concentration=info.get("conc_code") or concentration,
            concentration_name=concentration_name,
        )

        try:
            parsed = parse_audit(info["audit_xml"], degree)
        except Exception as error:
            tally.fail(code, error)
            return

        if parsed is None or parsed.catalog_year is None:
            tally.skip(code, "no DEGREE block or no catalog year")
            return
        if parsed.catalog_year < EARLIEST_CATALOG_YEAR:
            tally.outdated += 1
            tally.skip(code, f"catalog year {parsed.catalog_year}", announce=False)
            self.announce(f"Skipping {code}: catalog year {parsed.catalog_year}", level=2)
            return

        degree.year = parsed.catalog_year

        if self.dry_run:
            tally.saved += 1
            self.announce(
                f"Would save {degree} ({len(parsed.rules)} rules, {parsed.degree_credits} CU)"
            )
            return

        try:
            with transaction.atomic():
                Degree.objects.filter(
                    program=degree.program,
                    degree=degree.degree,
                    major=degree.major,
                    concentration=degree.concentration,
                    year=degree.year,
                ).delete()
                save_parsed_audit(parsed, degree)
                tally.majors += self.save_major(code, degree, parsed, concentration_name)
        except Exception as error:
            tally.fail(code, error)
            return

        tally.saved += 1
        self.announce(f"Saved {degree} ({len(parsed.rules)} rules, {degree.credits} CU)")

    def save_major(self, code, degree, parsed, concentration_name) -> int:
        """The same audit's MAJOR block, stored on its own. Returns how many were saved."""
        block = find_block(parsed, "MAJOR")
        if block is None:
            return 0

        Major.objects.filter(program_code=code, year=degree.year).delete()
        save_component(
            Major(
                program_code=code,
                code=block.req_value,
                name=degree.major_name,
                concentration=degree.concentration,
                concentration_name=concentration_name,
                year=degree.year,
            ),
            parsed,
            block,
        )
        return 1

    def fetch_minors(self, client, srcdb, tally):
        programs = client.minor_programs(srcdb)
        self.announce(f"srcdb {srcdb}: {len(programs)} minors")
        for program in programs:
            tally.minors += self.fetch_minor(client, srcdb, program, tally)

    def fetch_minor(self, client, srcdb, program, tally) -> int:
        """
        Loads one minor. The audit data wraps the MINOR block in a full degree, which is
        discarded: a minor contributes only its own block, and that block is marked
        STANDALONEBLOCK so its rules double count freely with the rest of a plan.
        """
        code = program["code"]
        try:
            info = client.program_info(code, srcdb)
            if not info:
                tally.skip(code, "no program info")
                return 0
            placeholder = Degree(
                program="AU_BA", degree="BA", major=info.get("majr_code") or "", year=0
            )
            parsed = parse_audit(info["audit_xml"], placeholder)
        except Exception as error:
            tally.fail(code, error)
            return 0

        block = find_block(parsed, "MINOR") if parsed else None
        if block is None or parsed.catalog_year is None:
            tally.skip(code, "no MINOR block or no catalog year")
            return 0
        if parsed.catalog_year < EARLIEST_CATALOG_YEAR:
            return 0

        name, _ = split_program_title(program["title"] or "", "MINOR")
        if self.dry_run:
            self.announce(f"Would save minor {code} ({block.credits} CU)")
            return 1

        try:
            with transaction.atomic():
                Minor.objects.filter(program_code=code, year=parsed.catalog_year).delete()
                save_component(
                    Minor(
                        program_code=code,
                        code=block.req_value,
                        name=name or None,
                        year=parsed.catalog_year,
                    ),
                    parsed,
                    block,
                )
        except Exception as error:
            tally.fail(code, error)
            return 0

        self.announce(f"Saved minor {code} ({block.credits} CU)")
        return 1
