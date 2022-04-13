from django.db.models.signals import post_save
from django.test.testcases import TestCase
from options.models import Option

from alert.management.commands.recomputestats import (
    deduplicate_status_updates,
    recompute_precomputed_fields,
)
from alert.models import AddDropPeriod
from courses.models import Building, Course, Meeting, Room, Section, StatusUpdate
from courses.util import get_or_create_course_and_section, invalidate_current_semester_cache
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
            5, StatusUpdate.objects.filter(section__course__semester=TEST_SEMESTER).count()
        )
        self.assertEqual(2, StatusUpdate.objects.filter(section__course__semester="2017C").count())
        deduplicate_status_updates(semesters="all")
        self.assertEqual(
            5, StatusUpdate.objects.filter(section__course__semester=TEST_SEMESTER).count()
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
            9, StatusUpdate.objects.filter(section__course__semester=TEST_SEMESTER).count()
        )
        self.assertEqual(3, StatusUpdate.objects.filter(section__course__semester="2017C").count())
        deduplicate_status_updates(semesters="all")
        self.assertEqual(
            5, StatusUpdate.objects.filter(section__course__semester=TEST_SEMESTER).count()
        )
        self.assertEqual(2, StatusUpdate.objects.filter(section__course__semester="2017C").count())


class RecomputePrecomputedFieldsTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.cis_160, self.cis_160_001 = create_mock_data("CIS-160-001", TEST_SEMESTER)
        building, _ = Building.objects.get_or_create(code=1)
        room, _ = Room.objects.get_or_create(building=building, number=1)
        new_meeting = Meeting(section=self.cis_160_001, day="R", start=11, end=12, room=room)
        new_meeting.save()
        self.cis_160_201 = create_mock_data("CIS-160-201", TEST_SEMESTER)[1]
        self.cis_160_201.activity = "REC"
        self.cis_160_201.save()
        self.cis_160_002 = create_mock_data("CIS-160-002", TEST_SEMESTER)[1]
        self.cis_120, self.cis_120_001 = create_mock_data("CIS-120-001", TEST_SEMESTER)
        self.cis_120_old, self.cis_120_001_old = create_mock_data("CIS-120-001", "2017C")

    def test_all_semesters(self):
        recompute_precomputed_fields()
        self.assertEquals(Course.objects.get(id=self.cis_160.id).num_activities, 2)
        self.assertEquals(Section.objects.get(id=self.cis_160_001.id).num_meetings, 4)
        self.assertEquals(Section.objects.get(id=self.cis_160_201.id).num_meetings, 3)
        self.assertEquals(Section.objects.get(id=self.cis_160_002.id).num_meetings, 3)

        self.assertEquals(Course.objects.get(id=self.cis_120.id).num_activities, 1)
        self.assertEquals(Section.objects.get(id=self.cis_120_001.id).num_meetings, 3)

        self.assertEquals(Course.objects.get(id=self.cis_120_old.id).num_activities, 1)
        self.assertEquals(Section.objects.get(id=self.cis_120_001_old.id).num_meetings, 3)
