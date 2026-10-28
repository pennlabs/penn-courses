from datetime import timedelta

from django.core.management import call_command
from django.db.models.signals import post_save
from django.test import TestCase
from django.utils import timezone
from options.models import Option

from alert.models import AddDropPeriod
from courses.management.commands.cache_course_reviews import REVIEW_FIELDS
from courses.models import Course, Section, course_reviews, sections_with_reviews
from courses.util import invalidate_current_semester_cache
from tests.courses.util import create_mock_data_with_reviews


TEST_SEMESTER = "2022A"
CACHED_VALUE = 1.5


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


class CachedReviewAveragesTestCase(TestCase):
    """
    Sets up one course/section with a fresh cache and one with an expired cache. Both caches hold
    CACHED_VALUE, which differs from the averages computed from their reviews.
    """

    def setUp(self):
        set_semester()
        self.fresh_course, self.fresh_section, _ = create_mock_data_with_reviews(
            "CIS-120-001", TEST_SEMESTER, 2
        )
        self.expired_course, self.expired_section, _ = create_mock_data_with_reviews(
            "CIS-121-001", TEST_SEMESTER, 2
        )
        self.future = timezone.now() + timedelta(days=1)
        past = timezone.now() - timedelta(days=1)
        cached = {f"precompute_{field}": CACHED_VALUE for field in REVIEW_FIELDS}
        for model, fresh, expired in [
            (Course, self.fresh_course, self.expired_course),
            (Section, self.fresh_section, self.expired_section),
        ]:
            model.objects.filter(id=fresh.id).update(annotation_expiration=self.future, **cached)
            model.objects.filter(id=expired.id).update(annotation_expiration=past, **cached)

    def live_course_averages(self, course):
        course = course_reviews(Course.objects.filter(id=course.id)).get()
        return {field: getattr(course, field) for field in REVIEW_FIELDS}

    def live_section_averages(self, section):
        section = sections_with_reviews(Section.objects.filter(id=section.id)).get()
        return {field: getattr(section, field) for field in REVIEW_FIELDS}


class CacheOrComputeReviewsTestCase(CachedReviewAveragesTestCase):
    def test_courses_use_cache_per_row(self):
        courses = {c.id: c for c in Course.with_reviews.all()}
        fresh = courses[self.fresh_course.id]
        expired = courses[self.expired_course.id]
        live = self.live_course_averages(self.expired_course)
        for field in REVIEW_FIELDS:
            self.assertEqual(getattr(fresh, field), CACHED_VALUE)
            self.assertIsInstance(getattr(fresh, field), float)
            self.assertNotEqual(live[field], CACHED_VALUE)
            self.assertAlmostEqual(getattr(expired, field), live[field])

    def test_sections_use_cache_per_row(self):
        sections = {s.id: s for s in Section.with_reviews.all()}
        fresh = sections[self.fresh_section.id]
        expired = sections[self.expired_section.id]
        live = self.live_section_averages(self.expired_section)
        for field in REVIEW_FIELDS:
            self.assertEqual(getattr(fresh, field), CACHED_VALUE)
            self.assertIsInstance(getattr(fresh, field), float)
            self.assertNotEqual(live[field], CACHED_VALUE)
            self.assertAlmostEqual(getattr(expired, field), live[field])

    def test_single_query(self):
        with self.assertNumQueries(1):
            list(Course.with_reviews.all())
        with self.assertNumQueries(1):
            list(Section.with_reviews.all())


class CacheCourseReviewsCommandTestCase(CachedReviewAveragesTestCase):
    def assert_cached(self, obj, expected, expiration_after):
        obj.refresh_from_db()
        for field in REVIEW_FIELDS:
            self.assertAlmostEqual(
                float(getattr(obj, f"precompute_{field}")), expected[field], places=3
            )
        self.assertGreater(obj.annotation_expiration, expiration_after)

    def test_recomputes_all_rows(self):
        courses = [self.fresh_course, self.expired_course]
        sections = [self.fresh_section, self.expired_section]
        live_courses = [self.live_course_averages(course) for course in courses]
        live_sections = [self.live_section_averages(section) for section in sections]
        call_command("cache_course_reviews")

        refreshed_after = timezone.now() + timedelta(days=29)
        for obj, expected in zip(courses + sections, live_courses + live_sections):
            self.assert_cached(obj, expected, refreshed_after)
