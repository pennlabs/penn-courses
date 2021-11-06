from django.db.models.signals import post_save
from django.test.testcases import TestCase
from options.models import Option

from alert.management.commands.recomputestats import deduplicate_status_updates
from alert.models import AddDropPeriod
from courses.models import StatusUpdate
from courses.util import get_or_create_course_and_section, invalidate_current_semester_cache


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
