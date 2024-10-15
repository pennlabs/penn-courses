from django.core.management.base import BaseCommand
from django.db.models import Q, Subquery

from courses.models import Course, Topic, Department, Instructor, Section
from review.annotations import annotate_average_and_recent
from review.util import get_average_and_recent_dict_single
from review.views import section_filters_pcr

from review.utils.pcs_client import PcsClient

pcs_client = PcsClient()

def get_department_objs():
    departments = Department.objects.all()
    for department in departments:
        yield {
            "code": department.code,
            "name": department.name
        }

def get_course_objs():
    topics = (
        Topic.objects.filter(most_recent__semester="2024A")
        .select_related("most_recent")
        .prefetch_related("most_recent__primary_listing__listing_set__sections__instructors")
    )
    for topic in topics:
        course = topic.most_recent
        crosslistings = ", ".join([c.full_code for c in course.crosslistings])
        all_instructors = list({instructor.name for s in course.sections.all() for instructor in s.instructors.all()})
        instructors = ", ".join(all_instructors[:min(len(all_instructors), 5)])
        course_qs = Course.objects.filter(pk=course.pk)
        course_qs = annotate_average_and_recent(
            course_qs,
            match_review_on=Q(section__course__topic=topic),
            match_section_on=Q(course__topic=topic) & section_filters_pcr,
            extra_metrics=True,
        )
        reviewed_course = (
            get_average_and_recent_dict_single(dict(course_qs.values()[0])) if course_qs else None
        )
        avg_reviews = reviewed_course["average_reviews"]
        yield {
            "code": course.full_code.replace("-", " "),
            "title": course.title,
            "crosslistings": crosslistings,
            "instructors": instructors,
            "description": course.description,
            "semester": course.semester,
            "course_quality": avg_reviews["rCourseQuality"]
            if "rCourseQuality" in avg_reviews
            else None,
            "difficulty": avg_reviews["rDifficulty"] if "rDifficulty" in avg_reviews else None,
            "work_required": avg_reviews["rWorkRequired"]
            if "rWorkRequired" in avg_reviews
            else None,
        }

def join_depts(depts):
    try:
        return ",".join(sorted(list(depts)))
    except TypeError:
        return ""

def get_instructor_objs():
    instructors = (
        Instructor.objects.filter(
            id__in=Subquery(Section.objects.filter(section_filters_pcr).values("instructors__id"))
        )
        .distinct()
        .values("name", "id", "section__course__department__code")
    )
    instructor_set = {}
    for inst in instructors:
        if inst["id"] not in instructor_set:
            instructor_set[inst["id"]] = {
                "title": inst["name"],
                "desc": set([inst["section__course__department__code"]]),
                "id": inst["id"],
            }
        instructor_set[inst["id"]]["desc"].add(inst["section__course__department__code"])
    
    for instructor in instructor_set.values():
        yield {
            "name": instructor["title"],
            "desc": join_depts(instructor["desc"]),
            "id": str(instructor["id"])
        }


def dump_autocomplete_data_to_redis(verbose=True):
    if verbose:
        print("\n=== Dumping data into Redis ===")
    pcs_client.clear_redis_db()
    if verbose:
        print("  Cleared Redis database...")
    pcs_client.initialize_redis_schema()
    if verbose:
        print("  Initialized Redis schema...")

    department_data = get_department_objs()
    if verbose:
        print("  Fetched departments...")
    course_data = get_course_objs()
    if verbose:
        print("  Fetched courses...")
    instructor_data = get_instructor_objs()
    if verbose:
        print("  Fetched instructors...")
    
    pcs_client.upload_data(department_data, 100)
    if verbose:
        print("  Uploaded departments...")
    pcs_client.upload_data(course_data, 25)
    if verbose:
        print("  Uploaded courses...")
    pcs_client.upload_data(instructor_data, 100)
    if verbose:
        print("  Uploaded instructors...")

    if verbose:
        print("=== Done ===")


class Command(BaseCommand):
    help = """Load in the courses' metadata into Redis for full-text searching"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Print out verbose information",
        )

    def handle(self, *args, **kwargs):
        verbose = kwargs["verbose"]
        dump_autocomplete_data_to_redis(verbose=verbose)