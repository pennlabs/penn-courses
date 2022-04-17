from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase
from options.models import Option
from rest_framework.test import APIClient

from alert.management.commands.recomputestats import recompute_precomputed_fields
from alert.models import AddDropPeriod
from courses.models import Course, Department, PreNGSSRequirement, Section, Topic, UserProfile
from courses.util import (
    get_or_create_course,
    get_or_create_course_and_section,
    invalidate_current_semester_cache,
    record_update,
    separate_course_code,
    set_crosslistings,
    update_course_from_record,
)
from tests.courses.util import create_mock_data


TEST_SEMESTER = "2022A"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


class SepCourseCodeTest(TestCase):
    def test_four_letter_dept_code(self):
        self.assertEqual(("ANTH", "3610", "401"), separate_course_code("ANTH3610401"))

    def test_three_letter_dept_code(self):
        self.assertEqual(("CIS", "1200", "001"), separate_course_code("CIS 1200001"))

    def test_two_letter_dept_code(self):
        self.assertEqual(("WH", "1100", "001"), separate_course_code("WH  1100001"))

    def test_four_letter_with_dashes(self):
        self.assertEqual(("PSCI", "110", "001"), separate_course_code("PSCI-110-001"))

    def test_three_letter_with_dashes(self):
        self.assertEqual(("CIS", "110", "001"), separate_course_code("CIS -110-001"))

    def test_two_letter_with_dashes(self):
        self.assertEqual(("WH", "110", "001"), separate_course_code("WH  -110-001"))

    def test_section_characters(self):
        self.assertEqual(("INTL", "2980", "BKC"), separate_course_code("INTL2980BKC"))

    def test_course_code_ends_in_character(self):
        self.assertEqual(("CRIM", "6004A", "301"), separate_course_code("CRIM6004A301"))

    def test_course_code_3_chars(self):
        self.assertEqual(("INTL", "BUL", "001"), separate_course_code("INTLBUL001"))

    def test_invalid_course(self):
        with self.assertRaises(ValueError):
            separate_course_code("BLAH BLAH BLAH")


class GetCourseSectionTest(TestCase):
    def setUp(self):
        self.c = Course(
            department=Department.objects.get_or_create(code="PSCI")[0],
            code="131",
            semester=TEST_SEMESTER,
            title="American Foreign Policy",
        )
        self.c.save()
        self.s = Section(code="001", course=self.c)
        self.s.save()

    def assertCourseSame(self, s):
        course, section, _, _ = get_or_create_course_and_section(s, TEST_SEMESTER)
        self.assertEqual(course, self.c, s)
        self.assertEqual(section, self.s, s)

    def test_get_course_exists_nodash(self):
        test_valid = [
            "PSCI131001",
            "PSCI 131 001",
            "PSCI 131001",
            "PSCI-131-001",
            "psci131001",
            "psci-131-001",
            "psci 131 001",
        ]
        for test in test_valid:
            self.assertCourseSame(test)

    def test_create_course(self):
        course, section, _, _ = get_or_create_course_and_section("CIS 120 001", TEST_SEMESTER)
        self.assertEqual("CIS-120-001", section.full_code)
        self.assertEqual(Course.objects.count(), 2)
        self.assertEqual(course.department.code, "CIS")
        self.assertEqual(course.code, "120")
        self.assertEqual(section.code, "001")


class CourseSaveAutoPrimaryListingTest(TestCase):
    def test_new(self):
        a, _ = get_or_create_course("CIS", "120", TEST_SEMESTER)
        a_db = Course.objects.get(full_code="CIS-120")
        self.assertEqual(a.primary_listing, a)
        self.assertEqual(a_db.primary_listing, a_db)

    def test_delete_max_id(self):
        get_or_create_course("CIS", "120", TEST_SEMESTER)
        get_or_create_course("CIS", "160", TEST_SEMESTER)
        c, _ = get_or_create_course("CIS", "121", TEST_SEMESTER)
        c.topic.delete()
        c.delete()
        d, _ = get_or_create_course("CIS", "240", TEST_SEMESTER)
        d_db = Course.objects.get(full_code="CIS-240")
        self.assertEqual(d.primary_listing, d)
        self.assertEqual(d_db.primary_listing, d_db)

    def test_delete_min_id(self):
        a, _ = get_or_create_course("CIS", "120", TEST_SEMESTER)
        get_or_create_course("CIS", "160", TEST_SEMESTER)
        get_or_create_course("CIS", "121", TEST_SEMESTER)
        a.topic.delete()
        a.delete()
        d, _ = get_or_create_course("CIS", "240", TEST_SEMESTER)
        d_db = Course.objects.get(full_code="CIS-240")
        self.assertEqual(d.primary_listing, d)
        self.assertEqual(d_db.primary_listing, d_db)

    def test_delete_all(self):
        a, _ = get_or_create_course("CIS", "120", TEST_SEMESTER)
        b, _ = get_or_create_course("CIS", "160", TEST_SEMESTER)
        c, _ = get_or_create_course("CIS", "121", TEST_SEMESTER)
        a.topic.delete()
        a.delete()
        b.topic.delete()
        b.delete()
        c.topic.delete()
        c.delete()
        d, _ = get_or_create_course("CIS", "240", TEST_SEMESTER)
        d_db = Course.objects.get(full_code="CIS-240")
        self.assertEqual(d.primary_listing, d)
        self.assertEqual(d_db.primary_listing, d_db)

    def test_set_primary_listing(self):
        get_or_create_course("CIS", "120", TEST_SEMESTER)
        b, _ = get_or_create_course("OIDD", "291", TEST_SEMESTER)
        c, _ = get_or_create_course("LGST", "291", TEST_SEMESTER, defaults={"primary_listing": b})
        b_db = Course.objects.get(full_code="OIDD-291")
        c_db = Course.objects.get(full_code="LGST-291")
        self.assertEqual(b.primary_listing, b)
        self.assertEqual(c.primary_listing, b)
        self.assertEqual(b_db.primary_listing, b_db)
        self.assertEqual(c_db.primary_listing, b_db)

    def test_set_primary_listing_id(self):
        get_or_create_course("CIS", "120", TEST_SEMESTER)
        b, _ = get_or_create_course("OIDD", "291", TEST_SEMESTER)
        c, _ = get_or_create_course(
            "LGST", "291", TEST_SEMESTER, defaults={"primary_listing_id": b.id}
        )
        b_db = Course.objects.get(full_code="OIDD-291")
        c_db = Course.objects.get(full_code="LGST-291")
        self.assertEqual(b.primary_listing, b)
        self.assertEqual(c.primary_listing, b)
        self.assertEqual(b_db.primary_listing, b_db)
        self.assertEqual(c_db.primary_listing, b_db)


class CourseTopicTestCase(TestCase):
    def test_new(self):
        a, _ = get_or_create_course("CIS", "120", TEST_SEMESTER)
        a_db = Course.objects.get(full_code="CIS-120")
        t = Topic.objects.get()
        self.assertEqual(a.topic, t)
        self.assertEqual(a_db.topic, t)
        self.assertEqual(t.most_recent, a_db)

    def test_existing_full_code(self):
        a, _ = get_or_create_course("CIS", "120", "2020C")
        b, _ = get_or_create_course("CIS", "120", TEST_SEMESTER)
        a_db = Course.objects.get(full_code="CIS-120", semester="2020C")
        b_db = Course.objects.get(full_code="CIS-120", semester=TEST_SEMESTER)
        t = Topic.objects.get()
        self.assertEqual(a.topic, t)
        self.assertEqual(a_db.topic, t)
        self.assertEqual(b.topic, t)
        self.assertEqual(b_db.topic, t)
        self.assertEqual(t.most_recent, b_db)

    def test_merge_with(self):
        a, _ = get_or_create_course("CIS", "120", "2020C")
        t = Topic.objects.get()
        b, _ = get_or_create_course("CIS", "1200", "2021C")
        t.merge_with(b.topic)
        c, _ = get_or_create_course("OIDD", "291", TEST_SEMESTER)
        get_or_create_course("LGST", "291", TEST_SEMESTER, defaults={"primary_listing": c})
        t1 = Topic.objects.filter(courses__full_code="CIS-120")[:1].get()
        t2 = Topic.objects.filter(courses__full_code="OIDD-291")[:1].get()
        t_merged = t1.merge_with(t2)
        a_db = Course.objects.get(full_code="CIS-120")
        b_db = Course.objects.get(full_code="CIS-1200")
        c_db = Course.objects.get(full_code="OIDD-291")
        d_db = Course.objects.get(full_code="LGST-291")
        t_merged_db = Topic.objects.filter(courses__full_code="CIS-120")[:1].get()
        self.assertEqual(t_merged, t_merged_db)
        self.assertEqual(a_db.topic, t_merged_db)
        self.assertEqual(b_db.topic, t_merged_db)
        self.assertEqual(c_db.topic, t_merged_db)
        self.assertEqual(d_db.topic, t_merged_db)
        self.assertEqual(t_merged.most_recent, c)
        self.assertEqual(t_merged_db.most_recent, c_db)

    def test_crosslistings(self):
        a, _ = get_or_create_course("CIS", "120", TEST_SEMESTER)
        b, _ = get_or_create_course("OIDD", "291", TEST_SEMESTER)
        c, _ = get_or_create_course("LGST", "291", TEST_SEMESTER, defaults={"primary_listing": b})
        a_db = Course.objects.get(full_code="CIS-120")
        b_db = Course.objects.get(full_code="OIDD-291")
        c_db = Course.objects.get(full_code="LGST-291")
        t1 = Topic.objects.get(courses__full_code="CIS-120")
        t2 = Topic.objects.filter(courses__full_code="OIDD-291")[:1].get()
        self.assertEqual(a.topic, t1)
        self.assertEqual(b.topic, t2)
        self.assertEqual(c.topic, t2)
        self.assertEqual(a_db.topic, t1)
        self.assertEqual(b_db.topic, t2)
        self.assertEqual(c_db.topic, t2)
        self.assertEqual(t1.most_recent, a_db)
        self.assertEqual(t2.most_recent, b_db)

    def test_crosslistings_exists_full_code(self):
        get_or_create_course("CIS", "120", "2020C")
        b, _ = get_or_create_course("OIDD", "291", "2020C")
        get_or_create_course("LGST", "291", "2020C", defaults={"primary_listing": b})
        d, _ = get_or_create_course("OIDD", "291", TEST_SEMESTER)
        get_or_create_course("MGMT", "291", TEST_SEMESTER, defaults={"primary_listing": d})
        get_or_create_course("OPIM", "291", TEST_SEMESTER, defaults={"primary_listing": d})
        a_db = Course.objects.get(full_code="CIS-120")
        b_db = Course.objects.get(full_code="OIDD-291", semester="2020C")
        c_db = Course.objects.get(full_code="LGST-291")
        d_db = Course.objects.get(full_code="OIDD-291", semester=TEST_SEMESTER)
        e_db = Course.objects.get(full_code="OPIM-291")
        f_db = Course.objects.get(full_code="MGMT-291")
        t1 = Topic.objects.get(courses__full_code="CIS-120")
        t2 = Topic.objects.filter(courses__full_code="OIDD-291")[:1].get()
        self.assertEqual(a_db.topic, t1)
        self.assertEqual(b_db.topic, t2)
        self.assertEqual(c_db.topic, t2)
        self.assertEqual(d_db.topic, t2)
        self.assertEqual(e_db.topic, t2)
        self.assertEqual(f_db.topic, t2)
        self.assertEqual(t1.most_recent, a_db)
        self.assertEqual(t2.most_recent, d_db)


class CourseStatusUpdateTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)

    def test_update_status(self):
        self.section.status = "C"
        self.section.save()
        up = record_update(self.section, TEST_SEMESTER, "C", "O", True, "JSON")
        up.save()
        update_course_from_record(up)
        _, section = create_mock_data(self.section.full_code, TEST_SEMESTER)
        self.assertEqual("O", section.status)


class SectionHasStatusUpdateTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.course, self.section = create_mock_data("CIS-120-001", TEST_SEMESTER)

    def test_no_updates(self):
        recompute_precomputed_fields()
        self.assertFalse(Section.objects.get(full_code="CIS-120-001").has_status_updates)

    def test_one_update(self):
        up = record_update(self.section, TEST_SEMESTER, "C", "O", True, "JSON")
        up.save()
        recompute_precomputed_fields()
        self.assertTrue(Section.objects.get(full_code="CIS-120-001").has_status_updates)

    def test_two_updates(self):
        up = record_update(self.section, TEST_SEMESTER, "C", "O", True, "JSON")
        up.save()
        up = record_update(self.section, TEST_SEMESTER, "O", "C", True, "JSON")
        up.save()
        recompute_precomputed_fields()
        self.assertTrue(Section.objects.get(full_code="CIS-120-001").has_status_updates)


class CrosslistingTestCase(TestCase):
    def setUp(self):
        self.anch, _ = create_mock_data("ANCH-027-401", TEST_SEMESTER)
        self.clst, _ = create_mock_data("CLST-027-401", TEST_SEMESTER)

    def test_add_primary_listing(self):
        set_crosslistings(self.anch, "")
        self.anch.save()
        self.assertEqual(self.anch, self.anch.primary_listing)

    def test_add_existing_class(self):
        set_crosslistings(self.clst, "ANCH-027-401")
        self.clst.save()
        clst, _ = create_mock_data("CLST-027-401", TEST_SEMESTER)
        anch, _ = create_mock_data("ANCH-027-401", TEST_SEMESTER)
        self.assertEqual(self.anch, clst.primary_listing)
        self.assertEqual(2, Course.objects.count())

    def test_crosslisting_set(self):
        set_crosslistings(self.clst, "ANCH-027-401")
        set_crosslistings(self.anch, "")
        self.clst.save()
        self.anch.save()
        self.assertTrue(self.anch in self.clst.crosslistings.all())
        self.assertTrue(self.clst in self.anch.crosslistings.all())

    def test_crosslisting_newsection(self):
        set_crosslistings(self.anch, "HIST-027-401")
        self.anch.save()
        self.assertEqual(3, Course.objects.count())


class RequirementTestCase(TestCase):
    def setUp(self):
        set_semester()
        get_or_create_course(
            "CIS", "120", "2012A"
        )  # dummy course to make sure we're filtering by semester
        self.course, _ = get_or_create_course("CIS", "120", TEST_SEMESTER)
        self.course2, _ = get_or_create_course("CIS", "125", TEST_SEMESTER)
        self.department = Department.objects.get(code="CIS")

        self.req1 = PreNGSSRequirement(
            semester=TEST_SEMESTER, school="SAS", code="TEST1", name="Test 1"
        )
        self.req2 = PreNGSSRequirement(
            semester=TEST_SEMESTER, school="SAS", code="TEST2", name="Test 2"
        )
        self.req3 = PreNGSSRequirement(semester="XXXXX", school="SAS", code="TEST1", name="Test 1+")

        self.req1.save()
        self.req2.save()
        self.req3.save()

        self.req1.departments.add(self.department)
        self.req1.overrides.add(self.course2)
        self.req2.courses.add(self.course)
        self.req2.courses.add(self.course2)
        self.req3.departments.add(self.department)

        self.client = APIClient()

    def assertCoursesEqual(self, expected, actual):
        def get_codes(x):
            sorted([f"{c.department.code}-{c.code}" for c in x])

        self.assertEqual(get_codes(expected), get_codes(actual))

    def test_requirements_nooverride(self):
        reqs = self.course.pre_ngss_requirements
        self.assertTrue(2, len(reqs))

    def test_requirements_override(self):
        reqs = self.course2.pre_ngss_requirements
        self.assertEqual(1, len(reqs))
        self.assertEqual(self.req2, reqs[0])

    def test_satisfying_courses(self):
        # make it so req1 has one department-level requirement, one course-level one,
        # and one override.
        c1, _ = get_or_create_course("MEAM", "101", TEST_SEMESTER)
        self.req1.courses.add(c1)
        courses = self.req1.satisfying_courses.all()
        self.assertEqual(2, len(courses))

        self.assertCoursesEqual([self.course, c1], courses)

    def test_override_precedent(self):
        # even if a course is in the list of courses, don't include it if it's in the
        # list of overrides
        self.req1.courses.add(self.course2)
        courses = self.req1.satisfying_courses.all()
        self.assertEqual(1, len(courses))
        self.assertCoursesEqual([self.course], courses)
        reqs = self.course2.pre_ngss_requirements
        self.assertEqual(1, len(reqs))
        self.assertEqual(self.req2, reqs[0])


class UserProfileTestCase(TestCase):
    def test_profile_created(self):
        u = User.objects.create_user(
            username="test", password="top_secret", email="test@example.com"
        )
        self.assertTrue(UserProfile.objects.filter(user=u).exists())
        p = UserProfile.objects.get(user=u)
        self.assertEqual(u.email, p.email)
