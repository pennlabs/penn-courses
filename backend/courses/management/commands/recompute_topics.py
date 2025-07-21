from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count, OuterRef, Subquery
from tqdm import tqdm

from courses.models import Course, Topic
from courses.util import all_semesters, historical_semester_probability


def garbage_collect_topics():
    """
    Deletes topics with no courses.
    """
    Topic.objects.annotate(num_courses=Count("courses")).filter(num_courses=0).delete()


def recompute_most_recent():
    """
    Recomputes the most_recent field for all Topics.
    """
    Topic.objects.update(
        most_recent_id=Subquery(
            Course.objects.filter(topic_id=OuterRef("id"))
            .order_by("-semester")
            .values("id")[:1]
        )
    )


def recompute_topics(
    min_semester: str = None, verbose=False, allow_null_parent_topic=True
):
    """
    Course topics are directly derived from the `Course.parent_course` graph.
        - Any course without a parent gets its own topic.
        - Any single child of a parent inherits the parent's topic.
        - Any child with siblings that exactly matches their parent in full_code
          and title inherits the parent's topic.
        - Any child with siblings that is the only child with a manually set
          parent_course_id inherits the parent topic.
        - Any child with siblings that does not exactly match their parent
          gets its own topic.
    These rules are applied sequentially in increasing order of semester.

    :param min_semester: The min semester from which to recompute topics. This function
        will reset topics for courses from all semesters since min_semester.
    :allow_null_parent_topic: If False, this script will error out if it encounters
        a None parent topic.
    :param verbose: Whether to print status/progress updates.
    """
    semesters = [
        sem for sem in all_semesters() if not min_semester or sem >= min_semester
    ]
    if verbose:
        print("Recomputing topics from the parent_course graph.")
    for i, semester in enumerate(sorted(semesters)):
        if verbose:
            print(f"Processing semester {semester} ({i+1}/{len(semesters)})...")
        with transaction.atomic():
            courses = list(
                Course.objects.filter(semester=semester)
                .select_related("parent_course", "parent_course__topic")
                .prefetch_related("parent_course__children")
                .order_by("-manually_set_parent_course")
            )
            topics_to_create = []
            topics_to_update = []  # .most_recent
            courses_to_update = []  # .topic
            visited_courses = set()

            for course in courses:
                if course.id in visited_courses:
                    continue
                parent = course.parent_course
                if not parent:
                    topics_to_create.append(Topic(most_recent=course))
                    continue
                if not parent.topic:
                    assert (
                        allow_null_parent_topic
                    ), f"Found parent {parent} of course {course} with no topic."
                    parent.topic = Topic(most_recent=parent)
                    parent.topic.save()
                    parent.save()
                branched_from = True
                if (
                    parent.full_code == course.full_code
                    and parent.title == course.title
                    or parent.children.count() == 1
                    or (
                        sum(
                            [
                                child.manually_set_parent_course
                                for child in parent.children.all()
                            ]
                        )
                        == 1
                        and course.manually_set_parent_course
                    )
                ):
                    # If a parent has multiple children and none are an exact match, we consider
                    # all the child courses as "branched from" the old. But if one child is an exact
                    # match, we inherit the parent's topic and the rest of the children
                    # are considered "branched from".
                    branched_from = False
                    if course.topic_id != parent.topic_id:
                        course.topic = parent.topic
                        course.topic.most_recent = course
                        topics_to_update.append(course.topic)
                        courses_to_update.append(course)
                for child in parent.children.all():
                    visited_courses.add(child.id)
                    if child.id == course.id and not branched_from:
                        continue
                    topics_to_create.append(
                        Topic(most_recent=child, branched_from=parent.topic)
                    )

            # Updating topics
            Topic.objects.bulk_update(
                topics_to_update,
                ["most_recent"],
                batch_size=4000,
            )

            # Creating topics
            course_id_to_topic = {
                topic.most_recent_id: topic
                for topic in Topic.objects.bulk_create(
                    topics_to_create,
                    batch_size=4000,
                )
            }
            for course in courses:
                if course.id in course_id_to_topic:
                    course.topic = course_id_to_topic[course.id]
                    courses_to_update.append(course)

            # Updating courses
            Course.objects.bulk_update(
                courses_to_update,
                ["topic"],
                batch_size=4000,
            )
    if verbose:
        print("Deleting empty topics...")
    garbage_collect_topics()
    if verbose:
        print("Recomputing most_recent links...")
    recompute_most_recent()
    if verbose:
        print(f"Finished recomputing topics for semesters >={min_semester}")


class Command(BaseCommand):
    help = "This script remakes Topics from the `parent_course` graph."

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-semester",
            type=str,
            help=(
                "The minimum semester from which to recompute topics. "
                "All semesters will be recomputed if None."
            ),
            default=None,
        )

    def handle(self, *args, **kwargs):
        print(
            "This script is atomic per-semester. "
            "If an error is encountered, all changes for that semester will be rolled back. "
            "Any changes made to previous semesters will persist."
        )

        min_semester = kwargs["min_semester"]
        if min_semester:
            assert (
                min_semester in all_semesters()
            ), f"--min-semester={min_semester} is not a valid semester."
        semesters = sorted(
            [sem for sem in all_semesters() if not min_semester or sem >= min_semester]
        )
        recompute_topics(
            min_semester, verbose=True, allow_null_parent_topic=bool(min_semester)
        )
        recompute_historical_semester_probabilities(
            current_semester=semesters[-1], verbose=True
        )


def recompute_historical_semester_probabilities(current_semester, verbose=False):
    """
    Recomputes the historical probabilities for all topics.
    """
    if verbose:
        print("Recomputing historical probabilities for all topics...")
    topics = Topic.objects.all()
    # Iterate over each Topic
    for i, topic in tqdm(enumerate(topics), disable=not verbose, total=topics.count()):
        # Calculate historical_year_probability for the current topic
        ordered_courses = topic.courses.all().order_by("semester")
        ordered_semester = [course.semester for course in ordered_courses]
        historical_prob = historical_semester_probability(
            current_semester, ordered_semester
        )
        # Update the historical_probabilities field for the current topic
        topic.historical_probabilities_spring = historical_prob[0]
        topic.historical_probabilities_summer = historical_prob[1]
        topic.historical_probabilities_fall = historical_prob[2]
        topic.save()
