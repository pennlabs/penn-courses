from django.db.models.signals import post_save
from django.test.testcases import TestCase
from options.models import Option

from alert.models import AddDropPeriod
from courses.management.commands.recompute_soft_state import (
    deduplicate_status_updates,
    recompute_course_credits,
    recompute_precomputed_fields,
)
from courses.models import Building, Course, Meeting, Room, Section, StatusUpdate
from courses.util import (
    all_semesters,
    get_or_create_course_and_section,
    invalidate_current_semester_cache,
)
from tests.courses.util import create_mock_data


TEST_SEMESTER = "2019A"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


class DeduplicateStatusUpdatesTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.sections = []
        self.sections.append(get_or_create_course_and_section("CIS-160-001", TEST_SEMESTER)[1])
        self.sections.append(get_or_create_course_and_section("CIS-160-002", TEST_SEMESTER)[1])
        self.sections.append(get_or_create_course_and_section("CIS-120-001", TEST_SEMESTER)[1])
        self.old_section = get_or_create_course_and_section("CIS-120-001", "2017C")[1]

    def test_no_duplicates(self):
        StatusUpdate(
            section=self.sections[0], old_status="", new_status="O", alert_sent=False
        ).save()
        StatusUpdate(
            section=self.sections[0], old_status="O", new_status="C", alert_sent=False
        ).save()
        StatusUpdate(
            section=self.sections[0], old_status="C", new_status="O", alert_sent=False
        ).save()

        StatusUpdate(
            section=self.sections[1], old_status="X", new_status="O", alert_sent=False
        ).save()
        StatusUpdate(
            section=self.sections[1], old_status="O", new_status="C", alert_sent=False
        ).save()

        StatusUpdate(
            section=self.old_section, old_status="C", new_status="O", alert_sent=False
        ).save()
        StatusUpdate(
            section=self.old_section, old_status="O", new_status="C", alert_sent=False
        ).save()

        self.assertEqual(
            5,
            StatusUpdate.objects.filter(section__course__semester=TEST_SEMESTER).count(),
        )
        self.assertEqual(2, StatusUpdate.objects.filter(section__course__semester="2017C").count())
        deduplicate_status_updates(semesters=list(all_semesters()))
        self.assertEqual(
            5,
            StatusUpdate.objects.filter(section__course__semester=TEST_SEMESTER).count(),
        )
        self.assertEqual(2, StatusUpdate.objects.filter(section__course__semester="2017C").count())

    def test_some_duplicates(self):
        StatusUpdate(
            section=self.sections[0], old_status="", new_status="O", alert_sent=False
        ).save()
        StatusUpdate(
            section=self.sections[0], old_status="", new_status="O", alert_sent=False
        ).save()
        StatusUpdate(
            section=self.sections[0], old_status="", new_status="O", alert_sent=False
        ).save()
        StatusUpdate(
            section=self.sections[0], old_status="O", new_status="C", alert_sent=False
        ).save()
        StatusUpdate(
            section=self.sections[0], old_status="O", new_status="C", alert_sent=False
        ).save()
        StatusUpdate(
            section=self.sections[0], old_status="C", new_status="O", alert_sent=False
        ).save()

        StatusUpdate(
            section=self.sections[1], old_status="X", new_status="O", alert_sent=False
        ).save()
        StatusUpdate(
            section=self.sections[1], old_status="X", new_status="O", alert_sent=False
        ).save()
        StatusUpdate(
            section=self.sections[1], old_status="O", new_status="C", alert_sent=False
        ).save()

        StatusUpdate(
            section=self.old_section, old_status="C", new_status="O", alert_sent=False
        ).save()
        StatusUpdate(
            section=self.old_section, old_status="O", new_status="C", alert_sent=False
        ).save()
        StatusUpdate(
            section=self.old_section, old_status="O", new_status="C", alert_sent=False
        ).save()

        self.assertEqual(
            9,
            StatusUpdate.objects.filter(section__course__semester=TEST_SEMESTER).count(),
        )
        self.assertEqual(3, StatusUpdate.objects.filter(section__course__semester="2017C").count())
        deduplicate_status_updates(semesters=list(all_semesters()))
        self.assertEqual(
            5,
            StatusUpdate.objects.filter(section__course__semester=TEST_SEMESTER).count(),
        )
        self.assertEqual(2, StatusUpdate.objects.filter(section__course__semester="2017C").count())


class RecomputePrecomputedFieldsTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.cis_160, self.cis_160_001 = create_mock_data("CIS-160-001", TEST_SEMESTER)
        self.cis_160_001.credits = 1.00
        self.cis_160_001.save()
        building, _ = Building.objects.get_or_create(code=1)
        room, _ = Room.objects.get_or_create(building=building, number=1)
        new_meeting = Meeting(section=self.cis_160_001, day="R", start=11, end=12, room=room)
        new_meeting.save()

        self.cis_160_201 = create_mock_data("CIS-160-201", TEST_SEMESTER)[1]
        self.cis_160_201.activity = "REC"
        self.cis_160_201.credits = 1.50
        self.cis_160_201.save()

        self.cis_160_002 = create_mock_data("CIS-160-002", TEST_SEMESTER)[1]
        self.cis_160_002.credits = 1.00
        self.cis_160_002.save()

        self.cis_120, self.cis_120_001 = create_mock_data("CIS-120-001", TEST_SEMESTER)
        self.cis_120_001.credits = 2.50
        self.cis_120_001.save()

        self.cis_120_old, self.cis_120_001_old = create_mock_data("CIS-120-001", "2017C")
        self.cis_120_001_old.credits = 3.00
        self.cis_120_001_old.save()

    def test_all_semesters(self):
        recompute_precomputed_fields()
        self.assertEquals(Course.objects.get(id=self.cis_160.id).num_activities, 2)
        self.assertEquals(Course.objects.get(id=self.cis_160.id).credits, 2.50)
        self.assertEquals(Section.objects.get(id=self.cis_160_001.id).num_meetings, 4)
        self.assertEquals(Section.objects.get(id=self.cis_160_201.id).num_meetings, 3)
        self.assertEquals(Section.objects.get(id=self.cis_160_002.id).num_meetings, 3)

        self.assertEquals(Course.objects.get(id=self.cis_120.id).num_activities, 1)
        self.assertEquals(Course.objects.get(id=self.cis_120.id).credits, 2.5)
        self.assertEquals(Section.objects.get(id=self.cis_120_001.id).num_meetings, 3)

        self.assertEquals(Course.objects.get(id=self.cis_120_old.id).num_activities, 1)
        self.assertEquals(Course.objects.get(id=self.cis_120_old.id).credits, 3)
        self.assertEquals(Section.objects.get(id=self.cis_120_001_old.id).num_meetings, 3)


class RecomputeCourseCreditsTestCase(TestCase):
    """
    Additional tests for recompute_course_credits
    """

    def setUp(self):
        self.course, self.section1, _, _ = get_or_create_course_and_section(
            "CIS-120-001", TEST_SEMESTER
        )
        _, self.section2, _, _ = get_or_create_course_and_section("CIS-120-101", TEST_SEMESTER)
        self.section1.activity = "LEC"
        self.section1.credits = 1.50
        self.section1.save()

        _, self.section2, _, _ = get_or_create_course_and_section("CIS-120-101", TEST_SEMESTER)
        self.section2.activity = "REC"
        self.section2.credits = 1.00
        self.section2.save()

        self.course2, self.section3, _, _ = get_or_create_course_and_section(
            "CIS-160-001", TEST_SEMESTER
        )
        self.section3.credits = 1.50
        self.section3.save()

        self.course3, self.section4, _, _ = get_or_create_course_and_section(
            "CIS-1210-001", TEST_SEMESTER
        )

        # Implictly testing that we exclude sections with code > 500
        _, self.section5, _, _ = get_or_create_course_and_section("CIS-1210-500", TEST_SEMESTER)
        self.section5.credits = 10.0

    def test_null_section_credits(self):
        self.assertIsNone(self.course3.credits)
        self.assertIsNone(self.section4.credits)

        recompute_course_credits()
        self.course3.refresh_from_db()

        self.assertIsNone(self.course3.credits)

    def test_single_section(self):
        self.assertIsNone(self.course2.credits)

        recompute_course_credits()
        self.course2.refresh_from_db()
        self.section3.refresh_from_db()
        self.assertEqual(self.course2.credits, self.section3.credits)

        self.section3.credits = 2.00
        self.section3.save()

        recompute_course_credits()
        self.course2.refresh_from_db()
        self.section3.refresh_from_db()
        self.assertEquals(self.course2.credits, self.section3.credits)
        self.assertEquals(self.course2.credits, 2.00)

    def test_many_activities(self):
        self.assertIsNone(self.course.credits)

        recompute_course_credits()
        self.course.refresh_from_db()
        self.assertEqual(self.course.credits, 2.50)

        self.section1.credits = 2.00
        self.section1.save()

        recompute_course_credits()
        self.course.refresh_from_db()
        self.assertEquals(self.course.credits, 3.00)

    def test_same_activity(self):
        self.section2.activity = "LEC"
        self.section2.save()

        recompute_course_credits()
        self.course.refresh_from_db()
        self.assertEqual(self.course.credits, 1.50)

    def test_same_activity_null_credits(self):
        # if we have 2 courses with same activity, where 1 has null credits
        _, null_section, _, _ = get_or_create_course_and_section("CIS-120-002", TEST_SEMESTER)
        self.assertIsNone(null_section.credits)
        recompute_course_credits()
        self.course.refresh_from_db()
        self.assertEqual(self.course.credits, 2.50)

        self.section1.credits = None
        self.section1.save()
        null_section.credits = 1.00
        null_section.save()

        recompute_course_credits()
        self.course.refresh_from_db()
        self.assertEqual(self.course.credits, 2.00)

    def test_excludes_sections_with_status_besides_closed_and_open(self):
        _, cancelled_section, _, _ = get_or_create_course_and_section("CIS-160-102", TEST_SEMESTER)
        cancelled_section.credits = 10.0
        cancelled_section.status = "X"
        recompute_course_credits()

        self.course2.refresh_from_db()
        self.assertEqual(self.course2.credits, 1.50)
