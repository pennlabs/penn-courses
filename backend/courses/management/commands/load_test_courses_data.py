import csv
import os

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from alert.models import AddDropPeriod
from courses.management.commands.export_test_courses_data import (
    models,
    related_id_fields,
    self_related_id_fields,
    semester_filter,
    test_data_fields,
    unique_identifying_fields,
)
from courses.util import get_add_drop_period


class Command(BaseCommand):
    help = (
        "Import test data (courses, sections, instructors, and reviews data) from the given csv. "
        "WARNING: this script will delete all pre-existing objects of the following datatypes "
        "from all semesters represented in the given csv (except for departments and instructors) "
        "if the import is successful:"
        f"\n{str([f for f in test_data_fields.keys() if f != 'instructors'])}."
        "\nIf an error is encountered at any point, you will be alerted and the database will "
        "remain as it was before this script was run.\n"
        "This script cannot be run in production."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--src",
            type=str,
            help="The file path of the .csv file containing the test data you want to import.",
        )

    def handle(self, *args, **kwargs):
        if "PennCourses.settings.development" not in os.environ["DJANGO_SETTINGS_MODULE"]:
            raise ValueError("This script cannot be run in a non-development environment.")
        src = os.path.abspath(kwargs["src"])
        _, file_extension = os.path.splitext(kwargs["src"])
        if not os.path.exists(src):
            return "File does not exist."
        if file_extension != ".csv":
            return "File is not a csv."

        fields = test_data_fields
        data_types = fields.keys()

        row_count = 0
        rows_map = {data_type: [] for data_type in data_types}
        # rows_map: maps datatype to list of rows for that datatype
        semesters = set()  # set of semesters represented in the given csv
        with open(src) as data_file:
            data_reader = csv.reader(data_file, delimiter=",", quotechar='"')
            for row in data_reader:
                data_type = row[0]
                if data_type in "courses":
                    semesters.add(row[2])
                assert data_type in data_types, (
                    f"Datatype {data_type} in the given csv is not valid for this version "
                    f"of the import script. Valid datatypes: {data_types}"
                )
                should_be = 6 if data_type.endswith("_m2mfield") else (1 + len(fields[data_type]))
                assert len(row) == should_be, (
                    f"The row {row} in the given csv is not valid for this version of the import "
                    f"script. Contains {len(row)} columns, while valid "
                    f"is {should_be}."
                )
                rows_map[data_type].append(row)
                row_count += 1
        objects = dict()  # maps datatype to object id to object
        to_save = {data_type: [] for data_type in data_types}
        # to_save: maps datatype to list of objects to save

        identify_id_map = {data_type: dict() for data_type in data_types}
        # identify_id_map: maps datatype to unique identification str to old id
        id_change_map = {data_type: dict() for data_type in data_types}
        # id_change_map: maps datatype to old id to new id
        self_related_ids = {data_type: dict() for data_type in data_types}
        # self_related_ids: maps datatype to field to object id to self-related object id

        def generate_unique_id_str_from_row(data_type, row):
            """
            Given a datatype and a row, generates a unique identification str
            """
            components = []
            for field in unique_identifying_fields[data_type]:
                field_value = row[1 + fields[data_type].index(field)]
                if data_type in related_id_fields and field in related_id_fields[data_type]:
                    field_value = id_change_map[related_id_fields[data_type][field]][field_value]
                components.append(field_value)
            return tuple(components)

        def generate_unique_id_str_from_object(data_type, object):
            """
            Given a datatype and an object, generates a unique identification str
            """
            components = []
            for field in unique_identifying_fields[data_type]:
                field_value = getattr(object, field)
                components.append(field_value)
            return tuple(components)

        print(
            "This script is atomic, meaning either all the test data from the given "
            "CSV will be loaded into the database, or otherwise if an error is encountered, "
            "all changes will be rolled back and the database will remain as it was "
            "before the script was run."
        )
        with transaction.atomic():
            print(f"Deleting existing objects from semesters {semesters}...")
            for data_type in data_types:
                if data_type not in semester_filter.keys():
                    continue
                models[data_type].objects.filter(
                    **{semester_filter[data_type] + "__in": list(semesters)}
                )
            for i, data_type in enumerate(data_types):
                print(f"Loading {data_type} data ({i+1}/{len(data_types)})...")
                for row in tqdm(rows_map[data_type]):
                    if data_type.endswith("_m2mfield"):
                        dtype = row[1]
                        object_id = id_change_map[dtype][row[2]]
                        object = objects[dtype][object_id]
                        related_dtype = row[5]
                        getattr(object, row[3]).add(id_change_map[related_dtype][row[4]])
                        continue
                    identify_id_map[data_type][
                        generate_unique_id_str_from_row(data_type, row)
                    ] = row[1]
                    field_to_index = {field: (1 + i) for i, field in enumerate(fields[data_type])}
                    to_save_dict = dict()  # this will be unpacked into the model initialization
                    for field in fields[data_type]:
                        if (
                            row[field_to_index[field]] is None
                            or row[field_to_index[field]] == "None"
                        ):
                            to_save_dict[field] = None
                            continue
                        if field == "id":
                            continue
                        if data_type in related_id_fields and field in related_id_fields[data_type]:
                            to_save_dict[field] = id_change_map[
                                related_id_fields[data_type][field]
                            ][row[field_to_index[field]]]
                        elif (
                            data_type in self_related_id_fields
                            and field in self_related_id_fields[data_type]
                        ):
                            to_save_dict[field] = None
                            if field not in self_related_ids[data_type]:
                                self_related_ids[data_type][field] = dict()
                            self_related_ids[data_type][field][row[field_to_index["id"]]] = row[
                                field_to_index[field]
                            ]
                        else:
                            to_save_dict[field] = row[field_to_index[field]]
                    to_save[data_type].append(models[data_type](**to_save_dict))

                if data_type not in semester_filter.keys() and data_type in models:
                    existing_objects = set(
                        generate_unique_id_str_from_object(data_type, m)
                        for m in models[data_type].objects.all()
                    )
                    to_save[data_type] = [
                        ob
                        for ob in to_save[data_type]
                        if generate_unique_id_str_from_object(data_type, ob) not in existing_objects
                    ]
                if data_type.endswith("_m2mfield"):
                    continue
                models[data_type].objects.bulk_create(to_save[data_type])
                objects[data_type] = dict()
                if data_type not in semester_filter.keys():
                    queryset = models[data_type].objects.all()
                else:
                    queryset = models[data_type].objects.filter(
                        **{semester_filter[data_type] + "__in": list(semesters)}
                    )
                for object in queryset:
                    if (
                        generate_unique_id_str_from_object(data_type, object)
                        not in identify_id_map[data_type]
                    ):
                        continue
                    objects[data_type][object.id] = object
                    id_change_map[data_type][
                        identify_id_map[data_type][
                            generate_unique_id_str_from_object(data_type, object)
                        ]
                    ] = object.id
                if data_type in self_related_ids.keys():
                    for field in self_related_ids[data_type].keys():
                        for self_id, other_id in self_related_ids[data_type][field].items():
                            self_new_id = id_change_map[data_type][self_id]
                            self_other_id = id_change_map[data_type][other_id]
                            setattr(objects[data_type][self_new_id], field, self_other_id)

            for semester in semesters:
                try:
                    get_add_drop_period(semester)
                except AddDropPeriod.DoesNotExist:
                    AddDropPeriod(semester=semester).save()

        print(f"Finished loading test data {src}... processed {row_count} rows. ")
