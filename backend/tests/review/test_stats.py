from dateutil.tz import gettz
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient

from alert.models import AddDropPeriod, Registration
from courses.management.commands.recompute_soft_state import (
    recompute_demand_distribution_estimates,
    recompute_precomputed_fields,
)
from courses.models import Instructor, Section
from courses.util import (
    get_or_create_add_drop_period,
    invalidate_current_semester_cache,
    record_update,
)
from PennCourses.settings.base import TIME_ZONE
from review.models import Review
from tests.courses.util import create_mock_data
from tests.review.test_api import PCRTestMixin, create_review


TEST_CURRENT_SEMESTER = "2021C"
TEST_SEMESTER = "2021A"  # Past semester for reviews

assert TEST_CURRENT_SEMESTER >= "2021C", "TEST_CURRENT_SEMESTER must be at least 2021C"
assert "b" not in TEST_CURRENT_SEMESTER.lower(), "TEST_CURRENT_SEMESTER cannot be a summer semester"
assert TEST_SEMESTER >= "2021A", "TEST_SEMESTER must be at least 2021A"
assert "b" not in TEST_SEMESTER.lower(), "TEST_SEMESTER cannot be a summer semester"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_CURRENT_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_CURRENT_SEMESTER).save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


"""
Below are some utility functions that make writing out the response.data dictionaries
a bit easier to do. All of the tests use instructor_quality as the reviewbit to test.
these helper functions cut down on a lot of the repeated characters in the responses.
"""


def ratings_dict(
    label,
    rInstructorQuality,
    rFinalEnrollment,
    rPercentOpen,
    rNumOpenings,
    rFilledInAdvReg,
):
    return {
        label: {
            "rInstructorQuality": rInstructorQuality,
            "rFinalEnrollment": rFinalEnrollment,
            "rPercentOpen": rPercentOpen,
            "rNumOpenings": rNumOpenings,
            "rFilledInAdvReg": rFilledInAdvReg,
        }
    }


def average(*fields):
    return ratings_dict("average_reviews", *fields)


def recent(*fields):
    return ratings_dict("recent_reviews", *fields)


def rating(*fields):
    return ratings_dict("ratings", *fields)


def set_registrations(section_id, registration_spec_list):
    for reg_spec in registration_spec_list:
        reg = Registration(section_id=section_id)
        reg.save()
        for key, value in reg_spec.items():
            setattr(reg, key, value)
        reg.save()


def get_sec_by_id(sec_id):
    return Section.objects.get(id=sec_id)


def get_start_end_duration(adp):
    start = adp.estimated_start
    end = adp.estimated_end
    duration = end - start
    return start, end, duration


def get_to_date_func(adp):
    start, end, duration = get_start_end_duration(adp)

    def to_date(percent):
        return start + percent * duration

    return to_date


class TwoSemestersOneInstructorTestCase(TestCase, PCRTestMixin):
    @classmethod
    def setUpTestData(cls):
        set_semester()
        cls.instructor_name = "Instructor One"
        create_review(
            "ESE-120-001",
            TEST_SEMESTER,
            cls.instructor_name,
            {"instructor_quality": 3.5},
        )
        create_review("ESE-120-001", "2020C", cls.instructor_name, {"instructor_quality": 2})
        cls.ESE_120_001_TEST_SEMESTER_id = Section.objects.get(
            full_code="ESE-120-001", course__semester=TEST_SEMESTER
        ).id
        cls.ESE_120_001_2020C_id = Section.objects.get(
            full_code="ESE-120-001", course__semester="2020C"
        ).id
        course, section = create_mock_data("ESE-120-001", TEST_CURRENT_SEMESTER)
        section.capacity = 100
        section.save()
        cls.current_sem_adp = get_or_create_add_drop_period(TEST_CURRENT_SEMESTER)
        cls.adp = get_or_create_add_drop_period(TEST_SEMESTER)
        AddDropPeriod(semester="2020C").save()
        cls.old_adp = get_or_create_add_drop_period("2020C")
        cls.average_instructor_quality = (2 + 3.5) / 2
        cls.recent_instructor_quality = 3.5
        cls.old_instructor_quality = 2
        old_status = "C"
        new_status = "O"
        start, end, duration = get_start_end_duration(cls.adp)
        for date in (
            [start - 3 * duration / 5, start - 2 * duration / 5, start - duration / 5]
            + [start + i * duration / 5 for i in range(1, 5)]
            + [
                start + 0.81 * duration,
                start + 0.82 * duration,
            ]
        ):
            # O[.2]C[.4]O[.6]C[.8]O[.81]C[.82]O
            record_update(
                Section.objects.get(id=cls.ESE_120_001_TEST_SEMESTER_id),
                TEST_SEMESTER,
                old_status,
                new_status,
                False,
                dict(),
                created_at=date,
            )
            old_status, new_status = new_status, old_status
        cls.recent_percent_open = 3 / 5 - 0.01
        cls.recent_filled_in_adv_reg = 0
        old_status = "O"
        new_status = "C"
        start, end, duration = get_start_end_duration(cls.old_adp)
        for date in [
            start - 3 * duration / 5,
            start - 2 * duration / 5,
            start - duration / 5,
        ] + [start + i * duration / 4 for i in range(1, 4)]:
            # C[.25]O[.5]C[.75]O
            record_update(
                Section.objects.get(id=cls.ESE_120_001_2020C_id),
                "2020C",
                old_status,
                new_status,
                False,
                dict(),
                created_at=date,
            )
            old_status, new_status = new_status, old_status
        cls.average_percent_open = (1 / 2 + 3 / 5 - 0.01) / 2
        cls.old_percent_open = 1 / 2
        cls.average_filled_in_adv_reg = 0.5
        cls.old_filled_in_adv_reg = 1
        to_date = get_to_date_func(cls.adp)
        # O[.2]C[.4]O[.6]C[.8]O[.81]C[.82]O
        registration_list_TS = [
            {
                "created_at": to_date(0.1),
                "cancelled_at": to_date(0.19),
                "cancelled": True,
            },
            {
                "created_at": to_date(0.15),
                "notification_sent_at": to_date(0.4),
                "notification_sent": True,
            },
            {
                "created_at": to_date(0.45),
                "notification_sent_at": to_date(0.6),
                "notification_sent": True,
            },
            {"created_at": to_date(0.61), "deleted_at": to_date(0.79), "deleted": True},
        ]
        set_registrations(cls.ESE_120_001_TEST_SEMESTER_id, registration_list_TS)
        to_date = get_to_date_func(cls.old_adp)
        # C[.25]O[.5]C[.75]O
        registration_list_2020C = [
            {
                "created_at": to_date(0.1001),
                "notification_sent_at": to_date(0.25),
                "notification_sent": True,
            },
            {
                "created_at": to_date(0.51),
                "cancelled_at": to_date(0.52),
                "deleted_at": to_date(0.53),
                "deleted": True,
            },
            {"created_at": to_date(0.76), "deleted_at": to_date(0.77), "deleted": True},
        ]
        set_registrations(cls.ESE_120_001_2020C_id, registration_list_2020C)

        cls.recent_num_updates = 3
        cls.average_num_updates = (3 + 2) / 2
        cls.old_num_updates = 2
        recent_review = Review.objects.get(section_id=cls.ESE_120_001_TEST_SEMESTER_id)
        recent_review.enrollment = 80
        recent_review.save()
        test_sem_class = get_sec_by_id(cls.ESE_120_001_TEST_SEMESTER_id)
        test_sem_class.capacity = 100
        test_sem_class.save()
        average_review = Review.objects.get(section_id=cls.ESE_120_001_2020C_id)
        average_review.enrollment = 99
        average_review.save()
        old_sem_class = get_sec_by_id(cls.ESE_120_001_2020C_id)
        old_sem_class.capacity = 100
        old_sem_class.save()
        cls.recent_enrollment = 80
        cls.average_enrollment = (80 + 99) / 2
        cls.old_enrollment = 99

        recompute_precomputed_fields()
        recompute_demand_distribution_estimates(
            semesters=[TEST_CURRENT_SEMESTER, TEST_SEMESTER, "2020C"]
        )

        local_tz = gettz(TIME_ZONE)
        cls.course_plots_subdict = {
            "code": "ESE-120",
            "current_add_drop_period": {
                "start": cls.current_sem_adp.estimated_start.astimezone(tz=local_tz),
                "end": cls.current_sem_adp.estimated_end.astimezone(tz=local_tz),
            },
            "average_plots": {
                "pca_demand_plot_since_semester": "2020C",
                "pca_demand_plot_num_semesters": 2,
                "percent_open_plot_since_semester": "2020C",
                "percent_open_plot_num_semesters": 2,
                "pca_demand_plot": [
                    (0, 0.0),
                    (0.1001, 0.25),
                    (0.2, 0.5),
                    (0.25, 0.25),
                    (0.4, 0.0),
                    (0.5, 0.25),
                    (0.6, 0.5),
                    (0.75, 0.25),
                    (0.8, 0.0),
                    (0.81, 0.25),
                    (0.82, 0.0),
                ],
                "percent_open_plot": [
                    (0, 0.5),
                    (0.2, 0),
                    (0.25, 0.5),
                    (0.4, 1),
                    (0.5, 0.5),
                    (0.6, 0.0),
                    (0.75, 0.5),
                    (0.8, 1),
                    (0.81, 0.5),
                    (0.82, 1),
                    (1, 1),
                ],
            },
            "recent_plots": {
                "pca_demand_plot_since_semester": TEST_SEMESTER,
                "pca_demand_plot_num_semesters": 1,
                "percent_open_plot_since_semester": TEST_SEMESTER,
                "percent_open_plot_num_semesters": 1,
                "pca_demand_plot": [
                    (0, 0.0),
                    (0.2, 0.5),
                    (0.4, 0.0),
                    (0.6, 0.5),
                    (0.8, 0.0),
                    (0.81, 0.5),
                    (0.82, 0.0),
                ],
                "percent_open_plot": [
                    (0, 1),
                    (0.2, 0.0),
                    (0.4, 1),
                    (0.6, 0.0),
                    (0.8, 1),
                    (0.81, 0),
                    (0.82, 1),
                    (1, 1),
                ],
            },
        }

    def setUp(self):
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))

    def test_course(self):
        reviews_subdict = {
            **average(
                self.average_instructor_quality,
                self.average_enrollment,
                self.average_percent_open,
                self.average_num_updates,
                self.average_filled_in_adv_reg,
            ),
            **recent(
                self.recent_instructor_quality,
                self.recent_enrollment,
                self.recent_percent_open,
                self.recent_num_updates,
                self.recent_filled_in_adv_reg,
            ),
        }
        self.assertRequestContainsAppx(
            "course-reviews",
            "ESE-120",
            {
                **reviews_subdict,
                "instructors": {Instructor.objects.get().pk: reviews_subdict},
            },
        )
        self.assertRequestContainsAppx(
            "course-plots",
            "ESE-120",
            self.course_plots_subdict,
        )

        instructor_ids = ",".join(str(id) for id in Instructor.objects.values_list("id", flat=True))
        self.assertRequestContainsAppx(
            "course-plots",
            "ESE-120",
            self.course_plots_subdict,
            query_params={
                "instructor_ids": instructor_ids,
            },
        )

    def test_instructor(self):
        subdict = {
            **average(
                self.average_instructor_quality,
                self.average_enrollment,
                self.average_percent_open,
                self.average_num_updates,
                self.average_filled_in_adv_reg,
            ),
            **recent(
                self.recent_instructor_quality,
                self.recent_enrollment,
                self.recent_percent_open,
                self.recent_num_updates,
                self.recent_filled_in_adv_reg,
            ),
        }
        self.assertRequestContainsAppx(
            "instructor-reviews",
            Instructor.objects.get().pk,
            {**subdict, "courses": {"ESE-120": subdict}},
        )

    def test_department(self):
        subdict = {
            **average(
                self.average_instructor_quality,
                self.average_enrollment,
                self.average_percent_open,
                self.average_num_updates,
                self.average_filled_in_adv_reg,
            ),
            **recent(
                self.recent_instructor_quality,
                self.recent_enrollment,
                self.recent_percent_open,
                self.recent_num_updates,
                self.recent_filled_in_adv_reg,
            ),
        }
        self.assertRequestContainsAppx(
            "department-reviews", "ESE", {"courses": {"ESE-120": subdict}}
        )

    def test_history(self):
        self.assertRequestContainsAppx(
            "course-history",
            ["ESE-120", Instructor.objects.get().pk],
            {
                "sections": [
                    rating(
                        self.recent_instructor_quality,
                        self.recent_enrollment,
                        self.recent_percent_open,
                        self.recent_num_updates,
                        self.recent_filled_in_adv_reg,
                    ),
                    rating(
                        self.old_instructor_quality,
                        self.old_enrollment,
                        self.old_percent_open,
                        self.old_num_updates,
                        self.old_filled_in_adv_reg,
                    ),
                ]
            },
        )

    def test_autocomplete(self):
        self.assertRequestContainsAppx(
            "review-autocomplete",
            [],
            {
                "instructors": [
                    {
                        "title": self.instructor_name,
                        "desc": "ESE",
                        "url": f"/instructor/{Instructor.objects.get().pk}",
                    }
                ],
                "courses": [
                    {
                        "title": "ESE-120",
                        "desc": [""],
                        "url": "/course/ESE-120",
                    }
                ],
                "departments": [{"title": "ESE", "desc": "", "url": "/department/ESE"}],
            },
        )

    def test_current_percent_open(self):
        self.assertAlmostEquals(
            self.recent_percent_open,
            Section.objects.get(id=self.ESE_120_001_TEST_SEMESTER_id).current_percent_open,
        )
        self.assertAlmostEquals(
            self.old_percent_open,
            Section.objects.get(id=self.ESE_120_001_2020C_id).current_percent_open,
        )


class OneReviewTestCase(TestCase, PCRTestMixin):
    @classmethod
    def setUpTestData(cls):
        set_semester()
        cls.instructor_name = "Instructor One"
        create_review(
            "ESE-120-001",
            TEST_SEMESTER,
            cls.instructor_name,
            {"instructor_quality": 3.5},
        )
        cls.ESE_120_001_id = Section.objects.get(full_code="ESE-120-001").id
        cls.instructor_quality = 3.5
        cls.current_sem_adp = get_or_create_add_drop_period(TEST_CURRENT_SEMESTER)
        cls.adp = get_or_create_add_drop_period(TEST_SEMESTER)
        start = cls.adp.estimated_start
        end = cls.adp.estimated_end
        duration = end - start
        old_status = "C"
        new_status = "O"
        percent_open_plot = [(0, 1)]
        for date in [
            start - 3 * duration / 7,
            start - 2 * duration / 7,
            start - duration / 7,
        ] + [start + i * duration / 7 for i in range(1, 7)]:
            # O[1/7]C[2/7]O[3/7]C[4/7]O[5/7]C[6/7]O
            percent_thru = cls.adp.get_percent_through_add_drop(date)
            record_update(
                Section.objects.get(id=cls.ESE_120_001_id),
                TEST_SEMESTER,
                old_status,
                new_status,
                False,
                dict(),
                created_at=date,
            )
            if date >= start:
                percent_open_plot.append((percent_thru, int(new_status == "O")))
            old_status, new_status = new_status, old_status
        percent_open_plot.append((1, 1))
        cls.percent_open = (duration * 4 / 7).total_seconds() / duration.total_seconds()
        cls.filled_in_adv_reg = 0
        to_date = get_to_date_func(cls.adp)
        set_registrations(
            cls.ESE_120_001_id,
            [
                {
                    "created_at": to_date(0.25),
                    "cancelled_at": to_date(0.26),
                    "cancelled": True,
                },
                {
                    "created_at": to_date(0.5),
                    "notification_sent_at": to_date(4 / 7),
                    "notification_sent": True,
                },
                {
                    "created_at": to_date(0.75),
                    "deleted_at": to_date(5.9 / 7),
                    "deleted": True,
                },
            ],
        )

        cls.num_updates = 3
        review = Review.objects.get()
        review.enrollment = 80
        review.save()
        sec = get_sec_by_id(cls.ESE_120_001_id)
        sec.capacity = 100
        sec.save()
        cls.enrollment = 80

        recompute_precomputed_fields()
        recompute_demand_distribution_estimates(semesters=[TEST_SEMESTER], verbose=True)

        plots = {
            "pca_demand_plot_since_semester": TEST_SEMESTER,
            "pca_demand_plot_num_semesters": 1,
            "percent_open_plot_since_semester": TEST_SEMESTER,
            "percent_open_plot_num_semesters": 1,
            "pca_demand_plot": [
                (0, 0),
                (0.25, 0.5),
                (2 / 7, 0),
                (3 / 7, 0.5),
                (4 / 7, 0),
                (5 / 7, 0.5),
                (6 / 7, 0),
                (1, 0),
            ],
            "percent_open_plot": percent_open_plot,
        }
        local_tz = gettz(TIME_ZONE)
        cls.course_plots_subdict = {
            "code": "ESE-120",
            "current_add_drop_period": {
                "start": cls.current_sem_adp.estimated_start.astimezone(tz=local_tz),
                "end": cls.current_sem_adp.estimated_end.astimezone(tz=local_tz),
            },
            "average_plots": plots,
            "recent_plots": plots,
        }

    def setUp(self):
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))

    def test_course(self):
        reviews_subdict = {
            **average(
                self.instructor_quality,
                self.enrollment,
                self.percent_open,
                self.num_updates,
                self.filled_in_adv_reg,
            ),
            **recent(
                self.instructor_quality,
                self.enrollment,
                self.percent_open,
                self.num_updates,
                self.filled_in_adv_reg,
            ),
        }

        instructor_ids = ",".join(
            [str(id) for id in [Instructor.objects.get().pk]],
        )
        self.assertRequestContainsAppx(
            "course-plots",
            ["ESE-120"],
            self.course_plots_subdict,
            query_params={
                "instructor_ids": instructor_ids,
            },
        )

        self.assertRequestContainsAppx(
            "course-reviews",
            "ESE-120",
            {
                **reviews_subdict,
                "instructors": {Instructor.objects.get().pk: reviews_subdict},
            },
        )

    def test_check_offered_in(self):
        instructor_ids = ",".join(
            [str(id) for id in [Instructor.objects.get().pk]],
        )
        self.assertRequestContainsAppx(
            "course-plots",
            ["ESE-120"],
            self.course_plots_subdict,
            query_params={"instructor_ids": instructor_ids, "semester": TEST_SEMESTER},
        )
        self.assertEqual(
            404,
            self.client.get(
                reverse("course-plots", args=["ESE-120"]),
                {"instructor_ids": instructor_ids, "semester": "2012A"},
            ).status_code,
        )

    def test_instructor(self):
        subdict = {
            **average(
                self.instructor_quality,
                self.enrollment,
                self.percent_open,
                self.num_updates,
                self.filled_in_adv_reg,
            ),
            **recent(
                self.instructor_quality,
                self.enrollment,
                self.percent_open,
                self.num_updates,
                self.filled_in_adv_reg,
            ),
        }
        self.assertRequestContainsAppx(
            "instructor-reviews",
            Instructor.objects.get().pk,
            {**subdict, "courses": {"ESE-120": subdict}},
        )

    def test_department(self):
        subdict = {
            **average(
                self.instructor_quality,
                self.enrollment,
                self.percent_open,
                self.num_updates,
                self.filled_in_adv_reg,
            ),
            **recent(
                self.instructor_quality,
                self.enrollment,
                self.percent_open,
                self.num_updates,
                self.filled_in_adv_reg,
            ),
        }
        self.assertRequestContainsAppx(
            "department-reviews", "ESE", {"courses": {"ESE-120": subdict}}
        )

    def test_history(self):
        self.assertRequestContainsAppx(
            "course-history",
            ["ESE-120", Instructor.objects.get().pk],
            {
                "sections": [
                    rating(
                        self.instructor_quality,
                        self.enrollment,
                        self.percent_open,
                        self.num_updates,
                        self.filled_in_adv_reg,
                    )
                ]
            },
        )

    def test_autocomplete(self):
        self.assertRequestContainsAppx(
            "review-autocomplete",
            [],
            {
                "instructors": [
                    {
                        "title": self.instructor_name,
                        "desc": "ESE",
                        "url": f"/instructor/{Instructor.objects.get().pk}",
                    }
                ],
                "courses": [
                    {
                        "title": "ESE-120",
                        "desc": [""],
                        "url": "/course/ESE-120",
                    }
                ],
                "departments": [{"title": "ESE", "desc": "", "url": "/department/ESE"}],
            },
        )


class TwoInstructorsOneSectionTestCase(TestCase, PCRTestMixin):
    @classmethod
    def setUpTestData(cls):
        set_semester()
        cls.instructor_1_name = "Instructor One"
        cls.instructor_2_name = "Instructor Two"
        create_review(
            "ESE-120-001",
            TEST_SEMESTER,
            cls.instructor_1_name,
            {"instructor_quality": 3.5},
        )
        create_review(
            "ESE-120-001",
            TEST_SEMESTER,
            cls.instructor_2_name,
            {"instructor_quality": 3.5},
        )
        cls.ESE_120_001_id = Section.objects.get(full_code="ESE-120-001").id
        cls.instructor_quality = 3.5
        cls.current_sem_adp = get_or_create_add_drop_period(TEST_CURRENT_SEMESTER)
        cls.adp = get_or_create_add_drop_period(TEST_SEMESTER)
        start = cls.adp.estimated_start
        end = cls.adp.estimated_end
        duration = end - start
        old_status = "C"
        new_status = "O"
        percent_open_plot = [(0, 1)]
        for date in [
            start - 3 * duration / 7,
            start - 2 * duration / 7,
            start - duration / 7,
        ] + [start + i * duration / 7 for i in range(1, 7)]:
            # O[1/7]C[2/7]O[3/7]C[4/7]O[5/7]C[6/7]O
            percent_thru = cls.adp.get_percent_through_add_drop(date)
            record_update(
                Section.objects.get(id=cls.ESE_120_001_id),
                TEST_SEMESTER,
                old_status,
                new_status,
                False,
                dict(),
                created_at=date,
            )
            if date >= start:
                percent_open_plot.append((percent_thru, int(new_status == "O")))
            old_status, new_status = new_status, old_status
        cls.filled_in_adv_reg = 0
        percent_open_plot.append((1, 1))
        to_date = get_to_date_func(cls.adp)
        set_registrations(
            cls.ESE_120_001_id,
            [
                {
                    "created_at": to_date(0.25),
                    "cancelled_at": to_date(0.26),
                    "cancelled": True,
                },
                {
                    "created_at": to_date(0.5),
                    "notification_sent_at": to_date(4 / 7),
                    "notification_sent": True,
                },
                {
                    "created_at": to_date(0.75),
                    "deleted_at": to_date(5.9 / 7),
                    "deleted": True,
                },
            ],
        )
        cls.percent_open = (duration * 4 / 7).total_seconds() / duration.total_seconds()

        cls.num_updates = 3
        for review in Review.objects.all():
            review.enrollment = 80
            review.save()
        sec = get_sec_by_id(cls.ESE_120_001_id)
        sec.capacity = 100
        sec.save()
        cls.enrollment = 80

        recompute_precomputed_fields()
        recompute_demand_distribution_estimates(semesters=[TEST_SEMESTER])

        plots = {
            "pca_demand_plot_since_semester": TEST_SEMESTER,
            "pca_demand_plot_num_semesters": 1,
            "percent_open_plot_since_semester": TEST_SEMESTER,
            "percent_open_plot_num_semesters": 1,
            "pca_demand_plot": [
                (0, 0),
                (0.25, 0.5),
                (2 / 7, 0),
                (3 / 7, 0.5),
                (4 / 7, 0),
                (5 / 7, 0.5),
                (6 / 7, 0),
                (1, 0),
            ],
            "percent_open_plot": percent_open_plot,
        }
        local_tz = gettz(TIME_ZONE)
        cls.course_plots_subdict = {
            "code": "ESE-120",
            "current_add_drop_period": {
                "start": cls.current_sem_adp.estimated_start.astimezone(tz=local_tz),
                "end": cls.current_sem_adp.estimated_end.astimezone(tz=local_tz),
            },
            "average_plots": plots,
            "recent_plots": plots,
        }
        empty_plots = {
            "pca_demand_plot_since_semester": None,
            "pca_demand_plot_num_semesters": 0,
            "percent_open_plot_since_semester": None,
            "percent_open_plot_num_semesters": 0,
            "pca_demand_plot": None,
            "percent_open_plot": None,
        }
        cls.empty_course_plots_subdict = {
            "code": "ESE-120",
            "current_add_drop_period": {
                "start": cls.current_sem_adp.estimated_start.astimezone(tz=local_tz),
                "end": cls.current_sem_adp.estimated_end.astimezone(tz=local_tz),
            },
            "average_plots": empty_plots,
            "recent_plots": empty_plots,
        }

    def setUp(self):
        self.client = APIClient()
        self.client.force_login(User.objects.create_user(username="test"))

    def test_course(self):
        reviews_subdict = {
            **average(
                self.instructor_quality,
                self.enrollment,
                self.percent_open,
                self.num_updates,
                self.filled_in_adv_reg,
            ),
            **recent(
                self.instructor_quality,
                self.enrollment,
                self.percent_open,
                self.num_updates,
                self.filled_in_adv_reg,
            ),
        }
        self.assertRequestContainsAppx(
            "course-reviews",
            "ESE-120",
            {
                **reviews_subdict,
                "instructors": {
                    Instructor.objects.get(name=self.instructor_1_name).pk: reviews_subdict,
                    Instructor.objects.get(name=self.instructor_2_name).pk: reviews_subdict,
                },
            },
        )
        self.assertRequestContainsAppx(
            "course-plots",
            "ESE-120",
            self.course_plots_subdict,
        )

        instructor_ids = ",".join(
            [
                str(id)
                for id in [
                    Instructor.objects.get(name=self.instructor_1_name).pk,
                    Instructor.objects.get(name=self.instructor_2_name).pk,
                ]
            ]
        )
        self.assertRequestContainsAppx(
            "course-plots",
            "ESE-120",
            self.course_plots_subdict,
            query_params={
                "instructor_ids": instructor_ids,
            },
        )

    def test_instructor(self):
        subdict = {
            **average(
                self.instructor_quality,
                self.enrollment,
                self.percent_open,
                self.num_updates,
                self.filled_in_adv_reg,
            ),
            **recent(
                self.instructor_quality,
                self.enrollment,
                self.percent_open,
                self.num_updates,
                self.filled_in_adv_reg,
            ),
        }
        self.assertRequestContainsAppx(
            "instructor-reviews",
            Instructor.objects.get(name=self.instructor_1_name).pk,
            {**subdict, "courses": {"ESE-120": subdict}},
        )
        self.assertRequestContainsAppx(
            "instructor-reviews",
            Instructor.objects.get(name=self.instructor_2_name).pk,
            {**subdict, "courses": {"ESE-120": subdict}},
        )

    def test_plots_invalid_instructor_ids(self):
        max_instructor_id = max(
            Instructor.objects.filter(
                name__in=[self.instructor_1_name, self.instructor_2_name]
            ).values_list("pk", flat=True)
        )
        instructor_ids = ",".join(
            [str(id) for id in [max_instructor_id + 1, max_instructor_id + 2]]
        )
        self.assertRequestContainsAppx(
            "course-plots",
            "ESE-120",
            self.empty_course_plots_subdict,
            query_params={
                "instructor_ids": instructor_ids,
            },
        )

    def test_plots_filter_to_one_instructor(self):
        self.assertRequestContainsAppx(
            "course-plots",
            "ESE-120",
            self.course_plots_subdict,
            query_params={
                "instructor_ids": str(Instructor.objects.get(name=self.instructor_1_name).id),
            },
        )
        self.assertRequestContainsAppx(
            "course-plots",
            "ESE-120",
            self.course_plots_subdict,
            query_params={
                "instructor_ids": str(Instructor.objects.get(name=self.instructor_2_name).id),
            },
        )

    def test_department(self):
        subdict = {
            **average(
                self.instructor_quality,
                self.enrollment,
                self.percent_open,
                self.num_updates,
                self.filled_in_adv_reg,
            ),
            **recent(
                self.instructor_quality,
                self.enrollment,
                self.percent_open,
                self.num_updates,
                self.filled_in_adv_reg,
            ),
        }
        self.assertRequestContainsAppx(
            "department-reviews", "ESE", {"courses": {"ESE-120": subdict}}
        )

    def test_history(self):
        self.assertRequestContainsAppx(
            "course-history",
            ["ESE-120", Instructor.objects.get(name=self.instructor_1_name).pk],
            {
                "sections": [
                    rating(
                        self.instructor_quality,
                        self.enrollment,
                        self.percent_open,
                        self.num_updates,
                        self.filled_in_adv_reg,
                    )
                ]
            },
        )
        self.assertRequestContainsAppx(
            "course-history",
            ["ESE-120", Instructor.objects.get(name=self.instructor_2_name).pk],
            {
                "sections": [
                    rating(
                        self.instructor_quality,
                        self.enrollment,
                        self.percent_open,
                        self.num_updates,
                        self.filled_in_adv_reg,
                    )
                ]
            },
        )

    def test_autocomplete(self):
        self.assertRequestContainsAppx(
            "review-autocomplete",
            [],
            {
                "instructors": [
                    {
                        "title": self.instructor_1_name,
                        "desc": "ESE",
                        "url": (
                            "/instructor/"
                            + str(Instructor.objects.get(name=self.instructor_1_name).pk)
                        ),
                    },
                    {
                        "title": self.instructor_2_name,
                        "desc": "ESE",
                        "url": (
                            "/instructor/"
                            + str(Instructor.objects.get(name=self.instructor_2_name).pk)
                        ),
                    },
                ],
                "courses": [
                    {
                        "title": "ESE-120",
                        "desc": [""],
                        "url": "/course/ESE-120",
                    }
                ],
                "departments": [{"title": "ESE", "desc": "", "url": "/department/ESE"}],
            },
        )


# TODO: More tests to add:
# 2 sections of same class
# 2 different classes in same semester
# classes that don't qualify
# classes with no registrations
# current / future classes?
