import csv
import os

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from courses.management.commands.export_test_courses_data import related_id_fields, test_data_fields
from courses.models import Course, Department, Instructor, Section
from review.models import Review, ReviewBit


class Command(BaseCommand):
    help = (
        "Import test data (courses, sections, instructors, and reviews data) from the given csv. "
        "WARNING: this script will delete all pre-existing objects of the following datatypes "
        "from all semesters represented in the given csv (except for departments and instructors) "
        "if the import is successful:"
        f"\n{str([f for f in test_data_fields.keys() if f != 'instructors'])}."
        "\nIf an error is encountered at any point, you will be alerted and the database will "
        "remain as it was before this script was run."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--src",
            type=str,
            help="The file path of the .csv file containing the test data you want to import.",
        )

    def handle(self, *args, **kwargs):
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
                if data_type in [
                    "courses_null_primary_listing",
                    "courses_non_null_primary_listing",
                ]:
                    semesters.add(row[1])
                assert data_type in data_types, (
                    f"Datatype {data_type} in the given csv is not valid for this version "
                    f"of the import script. Valid datatypes: {data_types}"
                )
                assert len(row) == 1 + len(fields[data_type]), (
                    f"The row {row} in the given csv is not valid for this version of the import "
                    f"script. Contains {len(row)} columns, while valid "
                    f"is {1 + len(fields[data_type])}."
                )
                rows_map[data_type].append(row)
                row_count += 1
        objects = dict()  # maps datatype to object id to object
        models = dict(
            {
                "departments": Department,
                "courses_null_primary_listing": Course,
                "courses_non_null_primary_listing": Course,
                "sections": Section,
                "instructors": Instructor,
                "reviews": Review,
                "review_bits": ReviewBit,
            }
        )
        to_save = {data_type: [] for data_type in data_types}
        # to_save: maps datatype to list of objects to save

        unique_identifying_fields = {
            "departments": ["code"],
            "courses_null_primary_listing": ["full_code", "semester"],
            "courses_non_null_primary_listing": ["full_code", "semester"],
            "sections": ["course_id", "code"],
            "instructors": ["name"],
            "reviews": ["section_id", "instructor_id"],
            "review_bits": ["review_id", "field"],
        }
        identify_id_map = {data_type: dict() for data_type in data_types}
        # identify_id_map: maps datatype to unique identification str to old id
        id_change_map = {data_type: dict() for data_type in data_types}
        # id_change_map: maps datatype to old id to new id

        def generate_unique_id_str_from_row(data_type, row):
            """
            Given a datatype and a row, generates a unique identification str
            """
            id_fields = unique_identifying_fields[data_type]
            indices = [1 + fields[data_type].index(field) for field in id_fields]
            id_field_indices = set(
                fields[data_type].index(field) for field in id_fields if field.endswith("_id")
            )
            return tuple(
                row[index] if index not in id_field_indices else id_change_map[row[index]]
                for index in indices
            )

        def generate_unique_id_str_from_object(data_type, object):
            """
            Given a datatype and an object, generates a unique identification str
            """
            id_fields = unique_identifying_fields[data_type]
            id_components = []
            for field in id_fields:
                field_value = getattr(object, field)
                id_components.append(field_value)
            return tuple(id_components)

        semester_filter = {
            "courses_null_primary_listing": "semester",
            "courses_non_null_primary_listing": "semester",
            "sections": "course__semester",
            "reviews": "section__course__semester",
            "review_bits": "review__section__course__semester",
        }

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
                    identify_id_map[generate_unique_id_str_from_row(data_type, row)] = row[0]
                    foreign_key_fields_to_model = dict()
                    if data_type in related_id_fields:
                        foreign_key_fields_to_model = related_id_fields[data_type]
                    field_to_index = {field: (1 + i) for i, field in enumerate(fields[data_type])}
                    to_save[data_type].append(
                        models[data_type](
                            **{
                                field: row[field_to_index[field]]
                                if field not in foreign_key_fields_to_model
                                else id_change_map[foreign_key_fields_to_model[field]][
                                    row[field_to_index[field]]
                                ]
                                for field in fields[data_type]
                            }
                        )
                    )

                for data_type in data_types:

                    if data_type not in semester_filter.keys():
                        existing_objects = set(
                            generate_unique_id_str_from_object(data_type, m)
                            for m in models[data_type].objects.all()
                        )
                        to_save[data_type] = [
                            ob
                            for ob in to_save[data_type]
                            if generate_unique_id_str_from_object(data_type, ob)
                            not in existing_objects
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
                        objects[data_type][object.id] = object
                        id_change_map[data_type][
                            identify_id_map[generate_unique_id_str_from_object(data_type, object)]
                        ] = object.id
                    if data_type == "courses_non_null_primary_listing":
                        objects["courses"] = {
                            **objects["courses_null_primary_listing"],
                            **objects["courses_non_null_primary_listing"],
                        }
                        id_change_map["courses"] = {
                            **id_change_map["courses_null_primary_listing"],
                            **id_change_map["courses_non_null_primary_listing"],
                        }

        print(f"Finished loading test data {src}... processed {row_count} rows. ")
