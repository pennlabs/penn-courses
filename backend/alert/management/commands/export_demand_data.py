import json
import os
from textwrap import dedent

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand
from django.db.models import F
from django.utils import timezone
from tqdm import tqdm

from alert.management.commands.recomputestats import recompute_precomputed_fields
from alert.models import Registration, Section, validate_add_drop_semester
from courses.models import StatusUpdate
from courses.util import (
    get_current_semester,
    get_or_create_add_drop_period,
    get_semesters,
)
from PennCourses.settings.base import (
    ROUGH_MINIMUM_DEMAND_DISTRIBUTION_ESTIMATES,
    S3_resource,
)
from review.views import extra_metrics_section_filters


def get_demand_data(semesters, section_query="", verbose=False):
    current_semester = get_current_semester()
    output_dict = dict()

    recompute_precomputed_fields(verbose=True)

    if verbose:
        print(f"Computing demand data for semesters {str(semesters)}...")
    for semester_num, semester in enumerate(semesters):
        try:
            validate_add_drop_semester(semester)
        except ValidationError:
            if verbose:
                print(f"Skipping semester {semester} (unsupported kind for stats).")
            continue
        add_drop_period = get_or_create_add_drop_period(semester)

        if verbose:
            print(f"Processing semester {semester}, " f"{(semester_num+1)}/{len(semesters)}.\n")

        output_dict[semester] = []  # list of demand data dicts
        section_id_to_object = dict()  # maps section id to section object (for this semester)
        volume_changes_map = dict()  # maps section id to list of volume changes
        status_updates_map = dict()  # maps section id to list of status updates

        iterator_wrapper = tqdm if verbose else (lambda x: x)
        if verbose:
            print("Indexing relevant sections...")
        for section in iterator_wrapper(
            Section.objects.filter(
                extra_metrics_section_filters,
                full_code__startswith=section_query,
                course__semester=semester,
            )
            .annotate(
                efficient_semester=F("course__semester"),
            )
            .distinct()
        ):
            section_id_to_object[section.id] = section
            volume_changes_map[section.id] = []
            status_updates_map[section.id] = []

        if verbose:
            print("Computing registration volume changes over time for each section...")
        for registration in iterator_wrapper(
            Registration.objects.filter(section_id__in=section_id_to_object.keys()).annotate(
                section_capacity=F("section__capacity")
            )
        ):
            section_id = registration.section_id
            volume_changes_map[section_id].append(
                {"date": registration.created_at, "volume_change": 1}
            )
            deactivated_at = registration.deactivated_at
            if deactivated_at is not None:
                volume_changes_map[section_id].append({"date": deactivated_at, "volume_change": -1})

        if verbose:
            print("Collecting status updates over time for each section...")
        for status_update in iterator_wrapper(
            StatusUpdate.objects.filter(
                section_id__in=section_id_to_object.keys(), in_add_drop_period=True
            )
        ):
            section_id = status_update.section_id
            status_updates_map[section_id].append(
                {
                    "date": status_update.created_at,
                    "old_status": status_update.old_status,
                    "new_status": status_update.new_status,
                }
            )

        if verbose:
            print("Joining updates for each section and sorting...")
        all_changes = sorted(
            [
                {"type": "status_update", "section_id": section_id, **update}
                for section_id, status_updates_list in status_updates_map.items()
                for update in status_updates_list
            ]
            + [
                {"type": "volume_change", "section_id": section_id, **change}
                for section_id, changes_list in volume_changes_map.items()
                for change in changes_list
            ],
            key=lambda x: (x["date"], int(x["type"] != "status_update")),
            # put status updates first on matching dates
        )

        # Initialize variables to be maintained in our main all_changes loop
        latest_popularity_dist_estimate = None
        registration_volumes = {section_id: 0 for section_id in section_id_to_object.keys()}
        demands = {section_id: 0 for section_id in section_id_to_object.keys()}

        # Initialize section statuses
        section_status = {section_id: None for section_id in section_id_to_object.keys()}
        for change in all_changes:
            section_id = change["section_id"]
            if change["type"] == "status_update":
                if section_status[section_id] is None:
                    section_status[section_id] = change["old_status"]

        percent_through = (
            add_drop_period.get_percent_through_add_drop(timezone.now())
            if semester == current_semester
            else 1
        )
        if percent_through == 0:
            if verbose:
                print(
                    f"Skipping semester {semester} because the add/drop period "
                    f"hasn't started yet."
                )
            continue
        distribution_estimate_threshold = sum(
            len(changes_list) for changes_list in volume_changes_map.values()
        ) // (ROUGH_MINIMUM_DEMAND_DISTRIBUTION_ESTIMATES * percent_through)
        num_changes_without_estimate = 0

        if verbose:
            print(f"Compiling demand data for semester {semester}...")
        for change in iterator_wrapper(all_changes):
            section_id = change["section_id"]

            if section_status[section_id] is None:
                section_status[section_id] = (
                    "O" if section_id_to_object[section_id].percent_open > 0.5 else "C"
                )
            if change["type"] == "status_update":
                section_status[section_id] = change["new_status"]
                continue

            date = change["date"]
            volume_change = change["volume_change"]
            registration_volumes[section_id] += volume_change
            demands[section_id] = (
                registration_volumes[section_id] / section_id_to_object[section_id].capacity
            )
            max_id = max(demands.keys(), key=lambda x: demands[x])
            min_id = min(demands.keys(), key=lambda x: demands[x])
            if (
                latest_popularity_dist_estimate is None
                or section_id == latest_popularity_dist_estimate["highest_demand_section"].id
                or section_id == latest_popularity_dist_estimate["lowest_demand_section"].id
                or latest_popularity_dist_estimate["highest_demand_section"].id != max_id
                or latest_popularity_dist_estimate["lowest_demand_section"].id != min_id
                or num_changes_without_estimate >= distribution_estimate_threshold
            ):
                num_changes_without_estimate = 0
                output_dict[semester].append(
                    {
                        "percent_through": percent_through,
                        "demands": [
                            val for sec_id, val in demands.items() if section_status[sec_id] == "C"
                        ],
                    }
                )

                latest_popularity_dist_estimate = {
                    "created_at": date,
                    "semester": semester,
                    "highest_demand_section": section_id_to_object[max_id],
                    "highest_demand_section_volume": registration_volumes[max_id],
                    "lowest_demand_section": section_id_to_object[min_id],
                    "lowest_demand_section_volume": registration_volumes[min_id],
                }
            else:
                num_changes_without_estimate += 1

    return output_dict


class Command(BaseCommand):
    help = dedent(
        """
        Export historical PCA demand data to a JSON file with the following schema:
        {
            semester: [{percent_through: int, demands: array of ints}, ...],
            ...
        }
        """
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            help="The path (local or in S3) you want to export to (must be a .json file).",
        )
        parser.add_argument(
            "--upload_to_s3",
            default=False,
            action="store_true",
            help=(
                "Enable this argument to upload the output of this script to the penn.courses "
                "S3 bucket, at the path specified by the path argument. "
            ),
        )
        parser.add_argument(
            "--section_query",
            default="",
            type=str,
            help=(
                "A prefix of the section full_code (e.g. CIS-120-001) to filter exported "
                "demand data by. Omit this argument to export demand data from all sections "
                "from the given semesters."
            ),
        )
        parser.add_argument(
            "--semesters",
            type=str,
            help=dedent(
                """
                The semesters argument should be a comma-separated list of semesters
            corresponding to the semesters from which you want to export demand data,
            i.e. "2019C,2020A,2020C" for fall 2019, spring 2020, and fall 2020.
            If you pass "all" to this argument, this script will export all demand data.
                """
            ),
            default="all",
        )

    def handle(self, *args, **kwargs):
        path = kwargs["path"]
        upload_to_s3 = kwargs["upload_to_s3"]
        semesters = get_semesters(kwargs["semesters"], verbose=True)
        if len(semesters) == 0:
            raise ValueError("No semesters provided for demand data export.")
        assert path.endswith(".json") or path == os.devnull
        script_print_path = ("s3://penn.courses/" if upload_to_s3 else "") + path
        print(
            f"Generating {script_print_path} with demand data data from "
            f"semesters {semesters}..."
        )
        output_file_path = "/tmp/export_demand_data.json" if upload_to_s3 else path
        with open(output_file_path, "w") as output_file:
            output_data = get_demand_data(
                semesters, section_query=kwargs["section_query"], verbose=True
            )
            json.dump(output_data, output_file)
        if upload_to_s3:
            S3_resource.meta.client.upload_file(output_file_path, "penn.courses", path)
            os.remove(output_file_path)
        print(f"Generated {script_print_path} with demand data from {len(semesters)} semesters.")
