from io import StringIO

from django.contrib.auth.models import User
from django.core import management
from django.db.models.functions import Lower
from django.test import TestCase

from courses.models import Instructor, Section
from courses.util import get_or_create_course_and_section
from review.management.commands.mergeinstructors import (
    INSTRUCTORS_UNMERGED,
    batch_duplicates,
    resolve_duplicates,
    strategies,
)
from review.models import Review


TEST_SEMESTER = "2022C"


class BatchDuplicateTestCase(TestCase):
    def setUp(self):
        Instructor.objects.create(name="A")
        Instructor.objects.create(name="a")
        Instructor.objects.create(name="b")

    def test_batch_duplicates(self):
        dupes = batch_duplicates(
            Instructor.objects.all().annotate(name_lower=Lower("name")),
            lambda x: x.name_lower,
        )
        self.assertEqual(1, len(dupes))
        self.assertEqual("a", dupes[0].pop().name.lower())

    def test_batch_duplicates_none_ignored(self):
        Instructor.objects.create(name="B")
        dupes = batch_duplicates(
            Instructor.objects.all().annotate(name_lower=Lower("name")),
            lambda x: x.name_lower if x.name_lower == "b" else None,
        )
        self.assertEqual(1, len(dupes))
        self.assertEqual("b", dupes[0].pop().name.lower())


class ResolveDuplicatesTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1")
        self.user2 = User.objects.create_user(username="user2")

        self.inst_A = Instructor.objects.create(name="A")
        self.inst_a = Instructor.objects.create(name="a")
        self.inst_b = Instructor.objects.create(name="b")

        self.course1, self.section1, _, _ = get_or_create_course_and_section("CIS-120-001", "2020C")
        self.course2, self.section2, _, _ = get_or_create_course_and_section("CIS-120-001", "2019C")

        self.review1 = Review.objects.create(section=self.section1, instructor=self.inst_A)
        self.section1.instructors.add(self.inst_A)

        self.review2 = Review.objects.create(section=self.section2, instructor=self.inst_a)
        self.section2.instructors.add(self.inst_a)

        self.stats = dict()

        def stat(key, amt=1, element=None):
            """
            Helper function to keep track of how many rows we are changing
            """
            value = self.stats.get(key, 0)
            if element is None:
                self.stats[key] = value + amt
            else:
                self.stats.setdefault(key, []).append(element)

        self.stat = stat

    def test_basic_merge(self):
        resolve_duplicates([{self.inst_A, self.inst_a}], False, self.stat)
        self.assertEqual(2, Instructor.objects.count())
        self.assertFalse(Instructor.objects.filter(name="A").exists())
        self.assertEqual(2, Review.objects.filter(instructor=self.inst_a).count())
        self.assertEqual(2, Section.objects.filter(instructors=self.inst_a).count())

    def test_basic_merge_dryrun_doesnt_modify(self):
        resolve_duplicates([{self.inst_A, self.inst_a}], True, self.stat)
        self.assertEqual(3, Instructor.objects.count())
        self.assertEqual(1, Review.objects.filter(instructor=self.inst_A).count())
        self.assertEqual(1, Section.objects.filter(instructors=self.inst_A).count())
        self.assertEqual(1, Review.objects.filter(instructor=self.inst_a).count())
        self.assertEqual(1, Section.objects.filter(instructors=self.inst_a).count())

    def test_merge_with_user(self):
        self.inst_A.user = self.user1
        self.inst_A.save()
        resolve_duplicates([{self.inst_A, self.inst_a}], False, self.stat)
        self.assertEqual(2, Instructor.objects.count())
        self.assertFalse(Instructor.objects.filter(name="a").exists())
        self.assertEqual(2, Review.objects.filter(instructor=self.inst_A).count())
        self.assertEqual(2, Section.objects.filter(instructors=self.inst_A).count())

    def test_merge_with_both_having_same_user(self):
        self.inst_a.user = self.user1
        self.inst_a.save()
        self.inst_A.user = self.user1
        self.inst_A.save()
        resolve_duplicates([{self.inst_A, self.inst_a}], False, self.stat)
        self.assertEqual(2, Instructor.objects.count())
        self.assertFalse(Instructor.objects.filter(name="a").exists())
        self.assertEqual(2, Review.objects.filter(instructor=self.inst_A).count())
        self.assertEqual(2, Section.objects.filter(instructors=self.inst_A).count())

    def test_merge_aborts_with_different_users(self):
        self.inst_a.user = self.user1
        self.inst_a.save()
        self.inst_A.user = self.user2
        self.inst_A.save()
        resolve_duplicates([{self.inst_A, self.inst_a}], False, self.stat)
        self.assertEqual(3, Instructor.objects.count())
        self.assertEqual(1, Review.objects.filter(instructor=self.inst_A).count())
        self.assertEqual(1, Section.objects.filter(instructors=self.inst_A).count())
        self.assertEqual(1, Review.objects.filter(instructor=self.inst_a).count())
        self.assertEqual(1, Section.objects.filter(instructors=self.inst_a).count())
        self.assertSetEqual(
            {self.inst_A.pk, self.inst_a.pk}, set(self.stats[INSTRUCTORS_UNMERGED][0])
        )


class MergeStrategyTestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="user1")
        self.user2 = User.objects.create_user(username="user2")

        self.inst_A = Instructor.objects.create(name="A")
        self.inst_a = Instructor.objects.create(name="a")
        self.inst_b = Instructor.objects.create(name="b")

    def test_case_insensitive(self):
        self.assertListEqual([{self.inst_a, self.inst_A}], strategies["case-insensitive"]())

    def test_case_insensitive_recent_first(self):
        self.inst_A.save()
        self.assertListEqual([{self.inst_A, self.inst_a}], strategies["case-insensitive"]())

    def test_pennid(self):
        self.inst_A.user = self.user1
        self.inst_A.save()
        self.inst_a.user = self.user1
        self.inst_a.save()
        self.assertListEqual([{self.inst_a, self.inst_A}], strategies["pennid"]())

    def test_flns_shared(self):
        _, cis_1600_001, _, _ = get_or_create_course_and_section("CIS-1600-001", TEST_SEMESTER)

        rajiv_no_middle = Instructor.objects.create(name="Rajiv Gandhi")
        rajiv_no_middle.user = self.user1
        rajiv_no_middle.save()
        cis_1600_001.instructors.add(rajiv_no_middle)

        rajiv_middle = Instructor.objects.create(name="Rajiv C. Gandhi")
        cis_1600_001.instructors.add(rajiv_middle)

        self.assertEqual(
            [{rajiv_no_middle, rajiv_middle}], strategies["first-last-name-sections"]()
        )

    def test_flns_not_shared(self):
        _, cis_1600_001, _, _ = get_or_create_course_and_section("CIS-1600-001", TEST_SEMESTER)

        rajiv_no_middle = Instructor.objects.create(name="Rajiv Gandhi")
        cis_1600_001.instructors.add(rajiv_no_middle)

        Instructor.objects.create(name="Rajiv C. Gandhi")

        self.assertEqual([], strategies["first-last-name-sections"]())


class MergeInstructorsCommandTestCase(TestCase):
    COMMAND_NAME = "mergeinstructors"

    def setUp(self):
        self.out = StringIO()
        self.err = StringIO()

        self.user1 = User.objects.create_user(username="user1")
        self.user2 = User.objects.create_user(username="user2")

        self.inst_A = Instructor.objects.create(name="A")
        self.inst_a = Instructor.objects.create(name="a")
        self.inst_b = Instructor.objects.create(name="b")

        self.course1, self.section1, _, _ = get_or_create_course_and_section("CIS-120-001", "2020C")
        self.course2, self.section2, _, _ = get_or_create_course_and_section("CIS-120-001", "2019C")

        self.review1 = Review.objects.create(section=self.section1, instructor=self.inst_A)
        self.section1.instructors.add(self.inst_A)

        self.review2 = Review.objects.create(section=self.section2, instructor=self.inst_a)
        self.section2.instructors.add(self.inst_a)

    def test_with_all_strats(self):
        self.inst_a.user = self.user1
        self.inst_b.user = self.user1
        self.inst_a.save()
        self.inst_b.save()
        management.call_command(
            self.COMMAND_NAME,
            "--all",
            stdout=self.out,
            stderr=self.err,
        )
        self.assertEqual(1, Instructor.objects.all().count())
        self.assertEqual(2, Review.objects.filter(instructor=self.inst_b).count())
        self.assertEqual(2, Section.objects.filter(instructors=self.inst_b).count())

    def test_with_one_strat(self):
        management.call_command(
            self.COMMAND_NAME,
            "--strategy=case-insensitive",
            stdout=self.out,
            stderr=self.err,
        )
        self.assertEqual(2, Instructor.objects.all().count())
        self.assertEqual(2, Review.objects.filter(instructor=self.inst_a).count())
        self.assertEqual(2, Section.objects.filter(instructors=self.inst_a).count())

    def test_with_manual_override(self):
        self.inst_A.user = self.user1
        self.inst_b.user = self.user2
        self.inst_A.save()
        self.inst_b.save()
        management.call_command(
            self.COMMAND_NAME,
            f"-i {self.inst_b.pk}",
            f"-i {self.inst_A.pk}",
            stdout=self.out,
            stderr=self.err,
        )
        self.assertEqual(2, Instructor.objects.all().count())
        self.assertFalse(Instructor.objects.filter(name="A").exists())
        self.assertEqual(1, Review.objects.filter(instructor=self.inst_a).count())
        self.assertEqual(1, Section.objects.filter(instructors=self.inst_a).count())

    def test_with_dry_run(self):
        self.inst_a.user = self.user1
        self.inst_b.user = self.user1
        self.inst_a.save()
        self.inst_b.save()
        management.call_command(
            self.COMMAND_NAME,
            "--all",
            "--dryrun",
            stdout=self.out,
            stderr=self.err,
        )
        self.assertEqual(3, Instructor.objects.all().count())
        self.assertEqual(0, Review.objects.filter(instructor=self.inst_b).count())
        self.assertEqual(0, Section.objects.filter(instructors=self.inst_b).count())
