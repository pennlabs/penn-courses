from io import StringIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import management
from django.core.management.base import CommandError
from django.db.models.signals import post_save
from django.test import TestCase
from options.models import Option

from alert.models import AddDropPeriod
from courses.models import Course, Instructor, Section
from courses.util import (
    get_or_create_course,
    get_or_create_course_and_section,
    import_instructor,
    invalidate_current_semester_cache,
)
from review.import_utils.import_to_db import (
    import_course_and_section,
    import_description_rows,
    import_summary_row,
)
from review.import_utils.parse_sql import entry_regex, parse_row
from review.models import Review, ReviewBit


TEST_SEMESTER = "2017A"
TEST_CURRENT_SEMESTER = "2018A"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_CURRENT_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_CURRENT_SEMESTER).save()


raw_summary = f"""
        Insert into PCRDEV.TEST_PCR_SUMMARY_V
        (SECTION_ID, TERM, INSTRUCTOR_PENN_ID, PRI_SECTION, TITLE,
        FORM_TYPE, INSTRUCTOR_FNAME, INSTRUCTOR_LNAME, ENROLLMENT, RESPONSES, RINSTRUCTORQUALITY,
        RCOURSEQUALITY, RDIFFICULTY)
        Values
        ('CIS 120001', '{TEST_SEMESTER}', '10000000', 'CIS 120001', 'COURSE TITLE', 1,
        'OLD', 'MCDONALD', 20, 15, 3.3, 2, 4);
            """

raw_ratings = f"""
Insert into PCRDEV.TEST_PCR_RATING_V
   (CONTEXT_NAME, SECTION_ID, TITLE, INSERT_DATE,
    INSTRUCTOR_NAME, INSTRUCTOR_PENN_ID, MEAN_TOTAL_RATING, MEDIAN_TOTAL_RATING, STANDARD_DEVIATION,
    TERM, TOTAL_RATING_0, TOTAL_RATING_1, TOTAL_RATING_2,
    TOTAL_RATING_3, TOTAL_RATING_4)
 Values
   ('Difficulty', 'CIS 120001', 'COURSE TITLE',
    TO_DATE('08/26/2013 21:35:19', 'MM/DD/YYYY HH24:MI:SS'),
    'MCDONALD,OLD', '10000000', 2.5, 2, 0.5,
    '{TEST_SEMESTER}', 0, 0, 4,
    2, 0);
"""

raw_descriptions = """
Insert into PCRDEV.TEST_PCR_COURSE_DESC_V
   (COURSE_ID, PARAGRAPH_NUMBER, COURSE_DESCRIPTION)
 Values
   ('CIS 120', '1', 'Hello, world!');
"""


class SQLParseTestCase(TestCase):
    def test_parse_key_value(self):
        query = """
        INSERT into DATABASE (a, b, c)
        VaLues (1, 'two', 'y''all');
        """
        expected = {"a": 1, "b": "two", "c": "y'all"}
        actual = parse_row(query)
        self.assertDictEqual(expected, actual)

    def test_regex_hyphen(self):
        query = """
        INSERT into DATABASE (a, b, c)
        VaLues (1, 'Chris Callison-Burch', 'y''all');
        """
        self.assertEqual(1, (len(entry_regex.findall(query))))

    def test_regex_hyphen_sequence(self):
        query = """
        INSERT into DATABASE (a, b, c)
        VaLues (1, 'Chris Callison-Burch', 'y''all');
        INSERT into DATABASE (a, b, c)
        VaLues (1, 'Chris:!!!***++++ Callison-Burch', 'y''all');
        """
        self.assertEqual(2, (len(entry_regex.findall(query))))

    def test_parse_summary(self):
        # Just make sure we're not throwing parse errors.
        parse = parse_row(raw_summary)
        self.assertIsInstance(parse, dict)

    def test_parse_ratings(self):
        parse = parse_row(raw_ratings)
        self.assertIsInstance(parse, dict)

    def test_parse_descriptions(self):
        parse = parse_row(raw_descriptions)
        expected = {
            "COURSE_ID": "CIS 120",
            "PARAGRAPH_NUMBER": "1",
            "COURSE_DESCRIPTION": "Hello, world!",
        }
        self.assertIsInstance(parse, dict)
        self.assertDictEqual(expected, parse)

    def test_semester_transformation(self):
        query = """
        INSERT into PCRDEV.TEST_PCR_COURSE_DESC_V
        (TERM) Values ('202230');
        """
        parse = parse_row(query)
        expected = {"TERM": "2022C"}
        self.assertDictEqual(parse, expected)


class ReviewImportTestCase(TestCase):
    def setUp(self):
        set_semester()
        self.row = {
            "SECTION_ID": "CIS 120001",
            "TERM": TEST_SEMESTER,
            "INSTRUCTOR_PENN_ID": "10000000",
            "PRI_SECTION": "CIS 120001",
            "TITLE": "COURSE TITLE",
            "FORM_TYPE": 1,
            "INSTRUCTOR_FNAME": "OLD",
            "INSTRUCTOR_LNAME": "MCDONALD",
            "ENROLLMENT": 20,
            "RESPONSES": 15,
            "RINSTRUCTORQUALITY": 3.3,
            "RCOURSEQUALITY": 2,
            "RDIFFICULTY": 4,
        }

        def stat(a, b=None):
            pass

        self.stat = stat

    def test_import_review(self):
        import_summary_row(self.row, self.stat)
        self.assertEqual(1, Course.objects.count())
        course = Course.objects.get()
        self.assertEqual("CIS-120", course.full_code)
        self.assertEqual(TEST_SEMESTER, course.semester)
        self.assertEqual(course.pk, course.primary_listing.pk)
        self.assertEqual(1, Section.objects.count())
        section = Section.objects.get()
        self.assertEqual("CIS-120-001", section.full_code)
        self.assertEqual(course.pk, section.course.pk)
        self.assertEqual(1, Instructor.objects.count())
        instructor = Instructor.objects.get()
        self.assertEqual("Old McDonald", instructor.name)
        self.assertEqual(1, section.instructors.all().count())
        self.assertTrue(section.instructors.all().filter(name="Old McDonald").exists())
        self.assertEqual(1, User.objects.count())
        self.assertEqual(1, Review.objects.count())
        review = Review.objects.get()
        self.assertEqual(section.pk, review.section.pk)
        self.assertEqual(instructor.pk, review.instructor.pk)
        self.assertEqual(3, ReviewBit.objects.count())

    def test_course_and_section_exist(self):
        """
        Make sure no duplite courses/sections get created, and that
        other values are overwritten accordingly.
        """
        get_or_create_course_and_section("CIS-120-001", TEST_SEMESTER)
        import_course_and_section(
            "CIS-120-001", TEST_SEMESTER, "title", "CIS-120-001", self.stat
        )
        self.assertEqual(1, Course.objects.count())
        course = Course.objects.get()
        self.assertEqual(1, Section.objects.count())
        self.assertEqual("title", course.title)
        self.assertEqual(course.pk, course.primary_listing.pk)

    def test_user_with_pennid_exist(self):
        user = User.objects.create(id=int("10000000"), username="ABC120")
        user.set_unusable_password()
        user.save()
        inst = import_instructor("10000000", "Old McDonald", self.stat)
        self.assertEqual(1, Instructor.objects.count())
        self.assertEqual(1, User.objects.count())
        self.assertEqual(user.pk, inst.user.pk)

    def test_instructor_name_exist(self):
        i1 = Instructor.objects.create(name="Old McDonald")
        i2 = import_instructor("10000000", "Old McDonald", self.stat)
        self.assertEqual(i1.pk, i2.pk)

    def test_instructor_name_user_pennid_exist(self):
        user = User.objects.create(id=int("10000000"), username="ABC120")
        user.set_unusable_password()
        user.save()
        inst = Instructor.objects.create(name="Old McDonald")
        inst2 = import_instructor("10000000", "Old McDonald", self.stat)
        user.refresh_from_db()
        inst.refresh_from_db()
        self.assertEqual(inst.pk, inst2.pk)
        self.assertEqual(user.pk, inst2.user.pk)


class DescriptionImportTestCase(TestCase):
    def test_one_paragraph(self):
        get_or_create_course("CIS", "120", TEST_SEMESTER)
        rows = [
            {
                "COURSE_ID": "CIS120",
                "PARAGRAPH_NUMBER": "1",
                "COURSE_DESCRIPTION": "Hello",
            }
        ]
        import_description_rows(len(rows), iter(rows), show_progress_bar=False)
        self.assertEqual(1, Course.objects.count())
        self.assertEqual("Hello", Course.objects.get().description)

    def test_no_course(self):
        rows = [
            {
                "COURSE_ID": "CIS120",
                "PARAGRAPH_NUMBER": "1",
                "COURSE_DESCRIPTION": "Hello",
            }
        ]
        import_description_rows(len(rows), iter(rows), show_progress_bar=False)
        self.assertEqual(0, Course.objects.count())

    def test_two_paragraphs(self):
        get_or_create_course("CIS", "120", TEST_SEMESTER)
        rows = [
            {
                "COURSE_ID": "CIS120",
                "PARAGRAPH_NUMBER": "2",
                "COURSE_DESCRIPTION": "world!",
            },
            {
                "COURSE_ID": "CIS120",
                "PARAGRAPH_NUMBER": "1",
                "COURSE_DESCRIPTION": "Hello",
            },
        ]
        import_description_rows(len(rows), iter(rows), show_progress_bar=False)
        self.assertEqual(1, Course.objects.count())
        self.assertEqual("Hello\nworld!", Course.objects.get().description)

    def test_two_semesters(self):
        get_or_create_course("CIS", "120", TEST_SEMESTER)
        get_or_create_course("CIS", "120", "3008A")

        rows = [
            {
                "COURSE_ID": "CIS120",
                "PARAGRAPH_NUMBER": "1",
                "COURSE_DESCRIPTION": "Hello",
            }
        ]
        import_description_rows(len(rows), iter(rows), show_progress_bar=False)
        self.assertEqual(2, Course.objects.count())
        c1 = Course.objects.get(semester=TEST_SEMESTER)
        c2 = Course.objects.get(semester="3008A")
        for c in [c1, c2]:
            self.assertEqual("Hello", c.description)

    def test_section_with_existing_description(self):
        get_or_create_course("CIS", "120", TEST_SEMESTER)
        get_or_create_course("CIS", "120", "3008A")
        c, _ = get_or_create_course("CIS", "120", "3005A")
        c.description = "TILL 3005"
        c.save()

        rows = [
            {
                "COURSE_ID": "CIS120",
                "PARAGRAPH_NUMBER": "1",
                "COURSE_DESCRIPTION": "Hello",
            }
        ]
        import_description_rows(len(rows), iter(rows), show_progress_bar=False)
        self.assertEqual(3, Course.objects.count())
        c1 = Course.objects.get(semester=TEST_SEMESTER)
        c2 = Course.objects.get(semester="3008A")
        for c in [c1, c2]:
            self.assertEqual("Hello", c.description)
        c3 = Course.objects.get(semester="3005A")
        self.assertEqual("TILL 3005", c3.description)

    def test_two_courses(self):
        get_or_create_course("CIS", "120", TEST_SEMESTER)
        get_or_create_course("CIS", "121", TEST_SEMESTER)
        rows = [
            {
                "COURSE_ID": "CIS120",
                "PARAGRAPH_NUMBER": "1",
                "COURSE_DESCRIPTION": "World",
            },
            {
                "COURSE_ID": "CIS121",
                "PARAGRAPH_NUMBER": "1",
                "COURSE_DESCRIPTION": "Hello",
            },
        ]
        import_description_rows(len(rows), iter(rows), show_progress_bar=False)
        c120 = Course.objects.get(code="120")
        c121 = Course.objects.get(code="121")
        self.assertEqual("World", c120.description)
        self.assertEqual("Hello", c121.description)


@patch("review.management.commands.iscimport.Command.close_files")
@patch("review.management.commands.iscimport.Command.get_files")
class ReviewImportCommandTestCase(TestCase):
    COMMAND_NAME = "iscimport"

    def setUp(self):
        set_semester()
        self.summary_fo = StringIO(raw_summary)
        self.ratings_fo = StringIO(raw_ratings)
        self.description_fo = StringIO(raw_descriptions)
        self.out = StringIO()
        self.err = StringIO()

    def test_successful_import(self, mock_get_files, mock_close_files):
        mock_get_files.return_value = [self.summary_fo]
        res = management.call_command(
            self.COMMAND_NAME,
            "hi.zip",
            "--zip",
            f"--semester={TEST_SEMESTER}",
            show_progress_bar=False,
            stdout=self.out,
            stderr=self.err,
        )
        self.assertEqual(0, res)
        for T in [Instructor, Course, Section, Review]:
            self.assertEqual(1, T.objects.count(), T)
        self.assertEqual(3, ReviewBit.objects.count(), ReviewBit.objects.all())

    def test_no_semester_defined(self, mock_get_files, mock_close_files):
        with self.assertRaises(CommandError):
            management.call_command(
                self.COMMAND_NAME,
                "hi.zip",
                "--zip",
                stdout=self.out,
                stderr=self.err,
                show_progress_bar=False,
            ),

    @patch("review.management.commands.iscimport.input")
    def test_reviews_exist_abort(self, input_mock, mock_get_files, mock_close_files):
        mock_get_files.return_value = [self.summary_fo]
        input_mock.return_value = "N"

        course, section, _, _ = get_or_create_course_and_section(
            "CIS 120001", TEST_SEMESTER
        )
        instructor = Instructor.objects.create(name="name")
        r = Review.objects.create(section=section, instructor=instructor)

        management.call_command(
            self.COMMAND_NAME,
            "hi.zip",
            "--zip",
            f"--semester={TEST_SEMESTER}",
            stdout=self.out,
            stderr=self.err,
            show_progress_bar=False,
        )
        self.assertEqual(1, Review.objects.count())
        self.assertEqual(r.pk, Review.objects.get().pk)

    @patch("review.management.commands.iscimport.input")
    def test_reviews_exist_continue(self, input_mock, mock_get_files, mock_close_files):
        mock_get_files.return_value = [self.summary_fo]
        input_mock.return_value = "Y"

        course, section, _, _ = get_or_create_course_and_section(
            "CIS 120001", TEST_SEMESTER
        )
        instructor = Instructor.objects.create(name="name")
        r = Review.objects.create(section=section, instructor=instructor)

        management.call_command(
            self.COMMAND_NAME,
            "hi.zip",
            "--zip",
            f"--semester={TEST_SEMESTER}",
            stdout=self.out,
            stderr=self.err,
            show_progress_bar=False,
        )
        self.assertEqual(1, Review.objects.count())
        self.assertNotEqual(r.pk, Review.objects.get().pk)

    def test_reviews_exist_force(self, mock_get_files, mock_close_files):
        mock_get_files.return_value = [self.summary_fo]

        course, section, _, _ = get_or_create_course_and_section(
            "CIS 120001", TEST_SEMESTER
        )
        instructor = Instructor.objects.create(name="name")
        r = Review.objects.create(section=section, instructor=instructor)

        management.call_command(
            self.COMMAND_NAME,
            "hi.zip",
            "--zip",
            f"--semester={TEST_SEMESTER}",
            "--force",
            stdout=self.out,
            stderr=self.err,
            show_progress_bar=False,
        )
        self.assertEqual(1, Review.objects.count())
        self.assertNotEqual(r.pk, Review.objects.get().pk)

    def test_import_details_bit_exists(self, mock_get_files, mock_close_files):
        mock_get_files.return_value = [self.summary_fo, self.ratings_fo]
        res = management.call_command(
            self.COMMAND_NAME,
            "hi.zip",
            "--zip",
            f"--semester={TEST_SEMESTER}",
            "--import-details",
            stdout=self.out,
            stderr=self.err,
            show_progress_bar=False,
        )
        self.assertEqual(0, res)
        c = Course.objects.get()
        self.assertEqual(c, c.primary_listing)
        for T in [Instructor, Course, Section, Review]:
            self.assertEqual(1, T.objects.count(), T)
        self.assertEqual(3, ReviewBit.objects.count())
        bit = ReviewBit.objects.get(field="difficulty")
        attrs = ["average", "median", "stddev"] + [f"rating{i}" for i in range(5)]
        for attr in attrs:
            self.assertIsNotNone(getattr(bit, attr))

        other_bit = ReviewBit.objects.get(field="instructor_quality")
        self.assertIsNotNone(other_bit.average)
        for attr in attrs[1:]:
            self.assertIsNone(getattr(other_bit, attr))

    def test_filter_semester(self, mock_get_files, mock_close_files):
        """
        Test that specifying a different semester will filter out
        other rows from the list before importing.
        """
        mock_get_files.return_value = [self.summary_fo, self.ratings_fo]
        res = management.call_command(
            self.COMMAND_NAME,
            "hi.zip",
            "--zip",
            "--semester=3008A",
            "--import-details",
            stdout=self.out,
            stderr=self.err,
            show_progress_bar=False,
        )
        self.assertEqual(0, res)
        for T in [Instructor, Course, Section, Review, ReviewBit]:
            self.assertEqual(0, T.objects.count())

    def test_load_descriptions_current_semester(self, mock_get_files, mock_close_files):
        mock_get_files.return_value = [self.summary_fo, self.description_fo]
        get_or_create_course("CIS", "120", "3008A")
        res = management.call_command(
            self.COMMAND_NAME,
            "hi.zip",
            "--zip",
            f"--semester={TEST_SEMESTER}",
            "--import-descriptions",
            stdout=self.out,
            stderr=self.err,
            show_progress_bar=False,
        )
        self.assertEqual(0, res)
        self.assertEqual(
            "Hello, world!", Course.objects.get(semester=TEST_SEMESTER).description
        )
        self.assertNotEqual(
            "Hello, world!", Course.objects.get(semester="3008A").description
        )

    def test_load_descriptions_all_semester(self, mock_get_files, mock_close_files):
        mock_get_files.return_value = [self.summary_fo, self.description_fo]
        get_or_create_course("CIS", "120", "3008A")
        res = management.call_command(
            self.COMMAND_NAME,
            "hi.zip",
            "--zip",
            "--all",
            "--import-descriptions",
            stdout=self.out,
            stderr=self.err,
            show_progress_bar=False,
        )
        self.assertEqual(0, res)
        self.assertEqual(
            "Hello, world!", Course.objects.get(semester=TEST_SEMESTER).description
        )
        self.assertEqual(
            "Hello, world!", Course.objects.get(semester="3008A").description
        )
