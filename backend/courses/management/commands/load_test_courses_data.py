import csv
import os
from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from alert.management.commands.recomputestats import recompute_stats
from courses.management.commands.export_test_courses_data import (
    models,
    related_id_fields,
    self_related_id_fields,
    semester_filter,
    test_data_fields,
    unique_identifying_fields,
)
from courses.models import Course, Topic
from courses.util import get_set_id, in_dev


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
        if not in_dev():
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
        self_related_ids = {data_type: defaultdict(dict) for data_type in data_types}
        # self_related_ids: maps datatype to field to object id to self-related object id
        deferred_related_ids = {data_type: defaultdict(dict) for data_type in data_types}
        # deferred_related_ids: maps datatype to field to object id to deferred related object id
        topic_id_to_course_uid_strs = defaultdict(set)
        # topic_id_to_course_uid_strs: maps old topic id to a set of course unique id strs

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
                ).delete()
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
                    unique_str = generate_unique_id_str_from_row(data_type, row)
                    identify_id_map[data_type][unique_str] = row[1]
                    field_to_index = {field: (1 + i) for i, field in enumerate(fields[data_type])}
                    to_save_dict = dict()  # this will be unpacked into the model initialization
                    for field in fields[data_type]:
                        if row[field_to_index[field]] is None or (
                            row[field_to_index[field]] == "None" and field != "prerequisites"
                        ):
                            to_save_dict[field] = None
                            continue
                        if field == "id":
                            continue
                        if data_type in related_id_fields and field in related_id_fields[data_type]:
                            related_data_type = related_id_fields[data_type][field]
                            if related_data_type in id_change_map:
                                # Related object has already been loaded
                                to_save_dict[field] = id_change_map[related_data_type][
                                    row[field_to_index[field]]
                                ]
                            else:
                                deferred_related_ids[data_type][field][
                                    row[field_to_index["id"]]
                                ] = row[field_to_index[field]]
                        elif (
                            data_type in self_related_id_fields
                            and field in self_related_id_fields[data_type]
                        ):
                            self_related_ids[data_type][field][row[field_to_index["id"]]] = row[
                                field_to_index[field]
                            ]
                        elif data_type == "courses" and field == "topic_id":
                            topic_id_to_course_uid_strs[row[field_to_index[field]]].add(unique_str)
                        else:
                            to_save_dict[field] = row[field_to_index[field]]
                    to_save[data_type].append(models[data_type](**to_save_dict))
                    ob = to_save[data_type][-1]
                    self_id = get_set_id(ob)
                    if data_type in self_related_id_fields:
                        for field in self_related_id_fields[data_type]:
                            # This self-related id will be changed later to the correct value
                            setattr(ob, field, self_id)

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

                objects[data_type] = dict()
                print(f"Saving {data_type} (this might take a while)...")
                models[data_type].objects.bulk_create(to_save[data_type])
                if data_type not in semester_filter.keys():
                    queryset = models[data_type].objects.all()
                else:
                    queryset = models[data_type].objects.filter(
                        **{semester_filter[data_type] + "__in": list(semesters)}
                    )
                for obj in queryset:
                    if (
                        generate_unique_id_str_from_object(data_type, obj)
                        not in identify_id_map[data_type]
                    ):
                        continue
                    objects[data_type][obj.id] = obj
                    id_change_map[data_type][
                        identify_id_map[data_type][
                            generate_unique_id_str_from_object(data_type, obj)
                        ]
                    ] = obj.id
                if data_type in self_related_ids.keys():
                    for field in self_related_ids[data_type].keys():
                        to_update = []
                        for self_id, other_id in self_related_ids[data_type][field].items():
                            self_new_id = id_change_map[data_type][self_id]
                            self_other_id = id_change_map[data_type][other_id]
                            obj = objects[data_type][self_new_id]
                            setattr(obj, field, self_other_id)
                            to_update.append(obj)
                        print(f"Updating {data_type} (this might take a while)...")
                        models[data_type].objects.bulk_update(to_update, [field])

            for data_type in deferred_related_ids.keys():
                if not deferred_related_ids[data_type]:
                    continue
                print(f"Loading deferred related fields for {data_type}...")
                for field in deferred_related_ids[data_type].keys():
                    related_data_type = related_id_fields[data_type][field]
                    to_update = []
                    for obj_id, related_id in deferred_related_ids[data_type][field].items():
                        obj_new_id = id_change_map[data_type][obj_id]
                        related_new_id = id_change_map[related_data_type][related_id]
                        obj = objects[data_type][obj_new_id]
                        setattr(obj, field, related_new_id)
                        to_update.append(obj)
                    print(f"Updating {data_type} (this might take a while)...")
                    models[data_type].objects.bulk_update(to_update, [field])

            print("Manually loading Topics...")
            # Assumes topics are only ever merged, not split
            for course_uid_strs in tqdm(topic_id_to_course_uid_strs.values()):
                course_ids = {
                    id_change_map["courses"][identify_id_map["courses"][uid_str]]
                    for uid_str in course_uid_strs
                }
                topics = list(
                    Topic.objects.filter(courses__id__in=course_ids)
                    .select_related("most_recent")
                    .distinct()
                )

                courses = Course.objects.filter(id__in=course_ids).select_related("primary_listing")
                most_recent = None
                for course in courses:
                    course = course.primary_listing
                    if not most_recent or course.semester > most_recent.semester:
                        most_recent = course

                if not topics:
                    topic = Topic(most_recent=most_recent)
                    topic.save()
                    Course.objects.filter(id__in=course_ids).update(topic=topic)
                    continue

                topic = Topic.merge_all(topics)

                Course.objects.filter(id__in=course_ids).update(topic=topic)
                if topic.most_recent != most_recent:
                    topic.most_recent = most_recent
                    topic.save()

            recompute_stats(
                semesters=sorted(list(semesters)), semesters_precomputed=True, verbose=True
            )

        print(f"Finished loading test data {src}... processed {row_count} rows. ")
