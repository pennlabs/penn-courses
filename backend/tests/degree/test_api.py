from django.db.models import Q
from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from options.models import Option
from rest_framework.test import APIClient

from alert.models import AddDropPeriod
from courses.models import Course, User
from courses.util import get_or_create_course_and_section, invalidate_current_semester_cache
from degree.models import (
    Degree,
    DegreePlan,
    DoubleCountRestriction,
    Fulfillment,
    PDPBetaUser,
    Rule,
    SatisfactionStatus,
)
from degree.serializers import SimpleCourseSerializer
from tests.courses.util import fill_course_soft_state


TEST_SEMESTER = "2023C"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()


class DegreeViewsetTest(TestCase):
    def test_list_degrees(self):
        pass


class DegreePlanViewsetTest(TestCase):
    def test_create_user_degree_plan(self):
        pass

    def test_list_user_degree_plan(self):
        pass

    def test_retrieve_user_degree_plan(self):
        pass

    def test_update_user_degree_plan(self):
        pass

    def test_patch_update_fulfillments(self):
        pass

    def test_invalid_fulfillment(self):
        pass

    def test_delete_user_degree_plan(self):
        pass

    def test_delete_user_degree_plan_with_fulfillments(self):
        pass


class FulfillmentViewsetTest(TestCase):
    def assertSerializedFulfillmentEquals(self, fulfillment: dict, expected: Fulfillment):
        self.assertEqual(len(fulfillment), 6)
        self.assertEqual(fulfillment["id"], expected.id)

        expected_course = SimpleCourseSerializer(
            Course.with_reviews.get(full_code=expected.full_code)
        ).data
        self.assertDictEqual(fulfillment["course"], expected_course)
        self.assertEqual(fulfillment["rules"], [rule.id for rule in expected.rules.all()])
        self.assertEqual(fulfillment["semester"], expected.semester)
        self.assertEqual(fulfillment["degree_plan"], expected.degree_plan.id)
        self.assertEqual(fulfillment["full_code"], expected.full_code)

    def setUp(self):
        self.user = User.objects.create_user(
            username="test", password="top_secret", email="test@example.com"
        )

        set_semester()

        # register the user as a beta user
        # TODO: remove after beta
        PDPBetaUser.objects.create(person=self.user)

        self.cis_1200, self.cis_1200_001, _, _ = get_or_create_course_and_section(
            "CIS-1200-001", TEST_SEMESTER, course_defaults={"credits": 1}
        )
        self.cis_1910, self.cis_1910_001, _, _ = get_or_create_course_and_section(
            "CIS-1910-001", TEST_SEMESTER, course_defaults={"credits": 0.5}
        )
        self.cis_1930, self.cis_1930_001, _, _ = get_or_create_course_and_section(
            "CIS-1920-001", TEST_SEMESTER, course_defaults={"credits": 1}
        )
        fill_course_soft_state()

        self.degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2023)
        self.parent_rule = Rule.objects.create()
        self.rule1 = Rule.objects.create(
            parent=self.parent_rule,
            q=repr(Q(full_code="CIS-1200")),
            num=1,
        )
        self.rule2 = Rule.objects.create(  # .5 cus / 1 course CIS-19XX classes
            parent=self.parent_rule,
            q=repr(Q(full_code__startswith="CIS-19")),
            credits=0.5,
            num=1,
        )
        self.rule3 = Rule.objects.create(  # 2 CIS classes
            parent=None,
            q=repr(Q(full_code__startswith="CIS")),
            num=2,
        )
        self.degree.rules.add(self.parent_rule, self.rule1, self.rule2, self.rule3)
        self.double_count_restriction = DoubleCountRestriction.objects.create(
            rule=self.rule2,  # CIS-19XX
            other_rule=self.rule3,  # CIS-XXXX
            max_credits=1,
        )
        self.degree_plan = DegreePlan.objects.create(
            name="Good Degree Plan",
            person=self.user,
        )
        self.degree_plan.degrees.add(self.degree)

        self.other_degree = Degree.objects.create(
            program="EU_BSE", degree="BSE", major="CMPE", year=2023
        )
        self.bad_degree_plan = DegreePlan.objects.create(
            name="Bad Degree Plan",
            person=self.user,
        )
        self.bad_degree_plan.degrees.add(self.other_degree)  # empty degree

        self.client = APIClient()
        self.client.force_login(self.user)

    def test_create_fulfillment(self):
        response = self.client.post(
            reverse("degreeplan-fulfillment-list", kwargs={"degreeplan_pk": self.degree_plan.id}),
            {"full_code": "CIS-1200", "semester": TEST_SEMESTER, "rules": [self.rule1.id]},
        )
        self.assertEqual(response.status_code, 201, response.json())
        self.assertSerializedFulfillmentEquals(
            response.data, Fulfillment.objects.get(full_code="CIS-1200")
        )

        fulfillment = Fulfillment.objects.get(full_code="CIS-1200")
        self.assertEqual(fulfillment.degree_plan, self.degree_plan)
        self.assertEqual(fulfillment.semester, TEST_SEMESTER)
        self.assertEqual(fulfillment.rules.count(), 1)
        self.assertEqual(fulfillment.rules.first(), self.rule1)
        satisfaction = SatisfactionStatus.objects.get(rule=self.rule1, degree_plan=self.degree_plan)
        self.assertTrue(satisfaction.satisfied)
        self.rule1.refresh_from_db()

    def test_list_fulfillment(self):
        a = Fulfillment(
            degree_plan=self.degree_plan,
            full_code="CIS-1200",
            semester=TEST_SEMESTER,
        )
        a.save()
        a.rules.add(self.rule1)
        b = Fulfillment(
            degree_plan=self.degree_plan,
            full_code="CIS-1910",
            semester=None,
        )
        b.save()
        b.rules.add(self.rule2)

        response = self.client.get(
            reverse("degreeplan-fulfillment-list", kwargs={"degreeplan_pk": self.degree_plan.id})
        )
        self.assertEqual(response.status_code, 200, response.json())
        response_a, response_b = sorted(
            (dict(d) for d in response.data), key=lambda d: d["full_code"]
        )

        self.assertSerializedFulfillmentEquals(response_a, a)
        self.assertSerializedFulfillmentEquals(response_b, b)

    def test_retrieve_fulfillment(self):
        a = Fulfillment(
            degree_plan=self.degree_plan,
            full_code="CIS-1200",
            semester=TEST_SEMESTER,
        )
        a.save()
        a.rules.add(self.rule1)

        response = self.client.get(
            reverse(
                "degreeplan-fulfillment-detail",
                kwargs={"degreeplan_pk": self.degree_plan.id, "full_code": a.full_code},
            )
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertSerializedFulfillmentEquals(response.data, a)

    def test_update_fulfillment_replace_rule(self):
        a = Fulfillment(
            degree_plan=self.degree_plan,
            full_code="CIS-1200",
            semester=TEST_SEMESTER,
        )
        a.save()
        a.rules.add(self.rule1)

        response = self.client.post(
            reverse(
                "degreeplan-fulfillment-list",
                kwargs={"degreeplan_pk": self.degree_plan.id},
            ),
            {"rules": [self.rule3.id], "full_code": a.full_code},
        )
        self.assertEqual(response.status_code, 200, response.json())
        self.assertSerializedFulfillmentEquals(response.data, a)
        a.refresh_from_db()
        self.assertEqual(a.rules.count(), 1)
        self.assertEqual(a.rules.first(), self.rule3)

    def test_update_semester(self):
        a = Fulfillment(
            degree_plan=self.degree_plan,
            full_code="CIS-1200",
            semester=None,
        )
        a.save()
        a.rules.add(self.rule1)

        response = self.client.post(
            reverse(
                "degreeplan-fulfillment-list",
                kwargs={"degreeplan_pk": self.degree_plan.id},
            ),
            {"semester": "2022B", "full_code": a.full_code},
        )
        self.assertEqual(response.status_code, 200, response.json())
        a.refresh_from_db()
        self.assertSerializedFulfillmentEquals(response.data, a)
        self.assertEqual(a.semester, "2022B")

    def test_trying_update_fulfillment_full_code_creates_fulfillment(self):
        a = Fulfillment(
            degree_plan=self.degree_plan,
            full_code="CIS-1200",
            semester=TEST_SEMESTER,
        )
        a.save()
        a.rules.add(self.rule3)

        response = self.client.post(
            reverse(
                "degreeplan-fulfillment-list",
                kwargs={"degreeplan_pk": self.degree_plan.id},
            ),
            {"full_code": "CIS-1910"},
        )
        self.assertEqual(response.status_code, 201, response.json())
        old_full_code = a.full_code

        # a doesn't update
        a.refresh_from_db()
        self.assertEqual(a.full_code, old_full_code)

    def test_update_fulfillment_rule(self):
        a = Fulfillment(
            degree_plan=self.degree_plan,
            full_code="CIS-1200",
            semester=TEST_SEMESTER,
        )
        a.save()
        a.rules.add(self.rule1)

        response = self.client.post(
            reverse(
                "degreeplan-fulfillment-list",
                kwargs={"degreeplan_pk": self.degree_plan.id},
            ),
            {"rules": [self.rule3.id, self.rule1.id], "full_code": a.full_code},
        )
        self.assertEqual(response.status_code, 200, response.json())
        a.refresh_from_db()
        self.assertSerializedFulfillmentEquals(response.data, a)
        self.assertEqual(a.rules.count(), 2)
        self.assertEqual(set(a.rules.all()), {self.rule1, self.rule3})

    def test_update_fulfillment_add_violated_rule(self):
        a = Fulfillment(
            degree_plan=self.degree_plan,
            full_code="CIS-1200",
            semester=TEST_SEMESTER,
        )
        a.save()
        a.rules.add(self.rule1)

        response = self.client.post(
            reverse(
                "degreeplan-fulfillment-list",
                kwargs={"degreeplan_pk": self.degree_plan.id},
            ),
            {"rules": [self.rule2.id, self.rule1.id], "full_code": a.full_code},
        )
        self.assertEqual(response.status_code, 400, response.json())
        self.assertEqual(
            response.data["non_field_errors"][0],
            f"Course CIS-1200 does not satisfy rule {self.rule2.id}",
        )

    def test_delete_fulfillment(self):
        a = Fulfillment(
            degree_plan=self.degree_plan,
            full_code="CIS-1200",
            semester=TEST_SEMESTER,
        )
        a.save()
        a.rules.add(self.rule1)
        response = self.client.delete(
            reverse(
                "degreeplan-fulfillment-detail",
                kwargs={"degreeplan_pk": self.degree_plan.id, "full_code": a.full_code},
            )
        )
        self.assertEqual(response.status_code, 204)

    def test_create_fulfillment_with_wrong_users_degreeplan(self):
        pass

    def test_create_fulfillment_with_nonexistant_degreeplan(self):
        pass

    def test_create_fulfillment_full_code_violates_rule(self):
        response = self.client.post(
            reverse(
                "degreeplan-fulfillment-list",
                kwargs={"degreeplan_pk": self.degree_plan.id},
            ),
            {"full_code": "CIS-1910", "rules": [self.rule1.id]},
        )
        self.assertEqual(response.status_code, 400, response.json())
        self.assertEqual(
            response.data["non_field_errors"][0],
            f"Course CIS-1910 does not satisfy rule {self.rule1.id}",
        )

    def test_create_fulfillment_with_denormalized_course_code(self):
        pass

    def test_create_fulfillment_with_double_count_violation(self):
        pass

    def test_update_fulfillment_with_rule_violation(self):
        pass

    def test_update_fulfillment_with_double_count_violation(self):
        pass

    def test_list_after_update(self):
        pass
