from django.db.models import Q
from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from courses.models import User
from courses.serializers import CourseListSerializer
from degree.serializers import DegreeSerializer, CourseTakenSerializer
from courses.util import get_or_create_course_and_section
from degree.models import (
    Degree,
    DegreePlan,
    DoubleCountRestriction,
    Fulfillment,
    Rule,
    SatisfactionStatus,
    UserProfile,
    DegreeProfile,
    CourseTaken,
)


TEST_SEMESTER = "2023C"


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
        self.assertEqual(
            fulfillment["course"], CourseListSerializer(expected.historical_course).data
        )
        self.assertEqual(fulfillment["rules"], [rule.id for rule in expected.rules.all()])
        self.assertEqual(fulfillment["semester"], expected.semester)
        self.assertEqual(fulfillment["degree_plan"], expected.degree_plan.id)
        self.assertEqual(fulfillment["full_code"], expected.full_code)

    def setUp(self):
        self.user = User.objects.create_user(
            username="test", password="top_secret", email="test@example.com"
        )
        self.cis_1200, self.cis_1200_001, _, _ = get_or_create_course_and_section(
            "CIS-1200-001", TEST_SEMESTER, course_defaults={"credits": 1}
        )
        self.cis_1910, self.cis_1910_001, _, _ = get_or_create_course_and_section(
            "CIS-1910-001", TEST_SEMESTER, course_defaults={"credits": 0.5}
        )
        self.cis_1930, self.cis_1930_001, _, _ = get_or_create_course_and_section(
            "CIS-1920-001", TEST_SEMESTER, course_defaults={"credits": 1}
        )

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
        self.assertEqual(fulfillment.historical_course, self.cis_1200)
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
                kwargs={"degreeplan_pk": self.degree_plan.id, "pk": a.id},
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

        response = self.client.patch(
            reverse(
                "degreeplan-fulfillment-detail",
                kwargs={"degreeplan_pk": self.degree_plan.id, "pk": a.id},
            ),
            {"rules": [self.rule3.id]},
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

        response = self.client.patch(
            reverse(
                "degreeplan-fulfillment-detail",
                kwargs={"degreeplan_pk": self.degree_plan.id, "pk": a.id},
            ),
            {"semester": "2022B"},
        )
        self.assertEqual(response.status_code, 200, response.json())
        a.refresh_from_db()
        self.assertSerializedFulfillmentEquals(response.data, a)
        self.assertEqual(a.semester, "2022B")

    def test_update_fulfillment_full_code(self):
        a = Fulfillment(
            degree_plan=self.degree_plan,
            full_code="CIS-1200",
            semester=TEST_SEMESTER,
        )
        a.save()
        a.rules.add(self.rule3)

        response = self.client.patch(
            reverse(
                "degreeplan-fulfillment-detail",
                kwargs={"degreeplan_pk": self.degree_plan.id, "pk": a.id},
            ),
            {"full_code": "CIS-1910"},
        )
        self.assertEqual(response.status_code, 200, response.json())
        a.refresh_from_db()
        self.assertSerializedFulfillmentEquals(response.data, a)
        self.assertEqual(a.full_code, "CIS-1910")

    def test_update_fulfillment_rule(self):
        a = Fulfillment(
            degree_plan=self.degree_plan,
            full_code="CIS-1200",
            semester=TEST_SEMESTER,
        )
        a.save()
        a.rules.add(self.rule1)

        response = self.client.patch(
            reverse(
                "degreeplan-fulfillment-detail",
                kwargs={"degreeplan_pk": self.degree_plan.id, "pk": a.id},
            ),
            {"rules": [self.rule3.id, self.rule1.id]},
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

        response = self.client.patch(
            reverse(
                "degreeplan-fulfillment-detail",
                kwargs={"degreeplan_pk": self.degree_plan.id, "pk": a.id},
            ),
            {"rules": [self.rule2.id, self.rule1.id]},
        )
        self.assertEqual(response.status_code, 400, response.json())
        self.assertEqual(
            response.data["non_field_errors"][0],
            f"Course CIS-1200 does not satisfy rule {self.rule2.id}",
        )

    def test_update_fulfillment_full_code_violates_rule(self):
        a = Fulfillment(
            degree_plan=self.degree_plan,
            full_code="CIS-1200",
            semester=TEST_SEMESTER,
        )
        a.save()
        a.rules.add(self.rule1)

        response = self.client.patch(
            reverse(
                "degreeplan-fulfillment-detail",
                kwargs={"degreeplan_pk": self.degree_plan.id, "pk": a.id},
            ),
            {"full_code": "CIS-1910"},
        )
        self.assertEqual(response.status_code, 400, response.json())
        self.assertEqual(
            response.data["non_field_errors"][0],
            f"Course CIS-1910 does not satisfy rule {self.rule1.id}",
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
                kwargs={"degreeplan_pk": self.degree_plan.id, "pk": a.id},
            )
        )
        self.assertEqual(response.status_code, 204)

    def test_create_fulfillment_with_wrong_users_degreeplan(self):
        pass

    def test_create_fulfillment_with_nonexistant_degreeplan(self):
        pass

    def test_create_fulfillment_with_rule_violation(self):
        pass

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


class DegreeProfileViewsetTest(TestCase):
    def assertSerializedDegreeProfileEquals(self, degreeprofile: dict, expected: DegreeProfile):
        self.assertEqual(len(degreeprofile), 5)
        self.assertEqual(degreeprofile["user_profile"], expected.user_profile.id)
        self.assertEqual(degreeprofile["graduation_date"], expected.graduation_date)

        expected_degrees = DegreeSerializer(expected.degrees.all(), many=True).data
        expected_courses_taken = CourseTakenSerializer(expected.coursetaken_set.all(), many=True).data

        self.assertEqual(
            degreeprofile["degrees"], expected_degrees
        )
        self.assertEqual(
            degreeprofile["courses_taken"], expected_courses_taken
        )

    def setUp(self):
        self.user = User.objects.create_user(
            username="ashley", password="hi", email="hi@example.com"
        )
        self.cis_1200, self.cis_1200_001, _, _ = get_or_create_course_and_section(
            "CIS-1200-001", TEST_SEMESTER, course_defaults={"credits": 1}
        )
        self.cis_1600, self.cis_1600_001, _, _ = get_or_create_course_and_section(
            "CIS-1600-001", TEST_SEMESTER, course_defaults={"credits": 1}
        )
        self.user_profile, _ = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={'email': self.user.email, 'push_notifications': False}
        )

        self.degree = Degree.objects.create(program="EU_BSE", degree="BSE", major="CIS", year=2023, credits=37)

        self.degree_profile = DegreeProfile.objects.create(
            user_profile=self.user_profile,
            graduation_date="2026A",
        )
        self.degree_profile.degrees.set([self.degree])

        CourseTaken.objects.create(degree_profile=self.degree_profile, course=self.cis_1600, semester=TEST_SEMESTER, grade="A+")

        self.client = APIClient()
        self.client.force_login(self.user)

    def test_get_queryset(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse(
                'degreeprofile-detail',
                kwargs={"pk": self.degree_profile.id}, 
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user_profile'], self.user_profile.id)

    def test_retrieve_degree_profile(self):
        new_user = User.objects.create_user(
            username="freshman", password="password", email="freshman@gmail.com"
        )
        self.client.force_authenticate(user=new_user)
        
        new_user_profile, _ = UserProfile.objects.get_or_create(
            user=new_user,
            defaults={'email': new_user.email, 'push_notifications': False}
        )

        new_degree_profile = DegreeProfile.objects.create(
            user_profile=new_user_profile,
            graduation_date="2027A",
        )
        new_degree_profile.degrees.set([self.degree]) 

        response = self.client.get(
            reverse(
                "degreeprofile-detail", 
                kwargs={"pk": new_degree_profile.id}, 
            )
        )

        self.assertEqual(response.status_code, 200, response.content)
        self.assertSerializedDegreeProfileEquals(response.data, new_degree_profile)

    def test_update_degrees(self):
        """
        Replaces degrees with ones included in request
        """
        self.client.force_authenticate(user=self.user)
        new_degree = Degree.objects.create(program="EU_BSE", degree="BS", major="MEAM", year=2023, credits=37)
        update_data = {
            "degrees": [new_degree.id],
        }
        
        response = self.client.patch(
            reverse("degreeprofile-detail", kwargs={"pk": self.degree_profile.id}),
            data=update_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200, response.content)
        self.degree_profile.refresh_from_db()
        updated_degrees = list(self.degree_profile.degrees.values_list('id', flat=True))
        self.assertEqual(updated_degrees, [new_degree.id])

    def test_add_course(self):
        self.client.force_authenticate(user=self.user)
        add_course_data = {
            "course": self.cis_1200.id, 
            "semester": TEST_SEMESTER,
            "grade": "A"
        }
        
        response = self.client.post(
            reverse("degreeprofile-add_course", kwargs={"pk": self.degree_profile.id}),
            data=add_course_data,
            format='json'
        )
        
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(
            CourseTaken.objects.filter(
                degree_profile=self.degree_profile, 
                course=self.cis_1200.id, 
                semester=TEST_SEMESTER, 
                grade="A"
            ).exists()
        )

    def test_remove_course(self):
        self.client.force_authenticate(user=self.user)
        CourseTaken.objects.create(
            degree_profile=self.degree_profile, 
            course=self.cis_1600, 
            semester="2024A", 
            grade="F"
        )

        remove_course_data = {
            "course": self.cis_1600.id,
            "semester": "2024A"
        }

        response = self.client.post(
            reverse("degreeprofile-remove_course", kwargs={"pk": self.degree_profile.id}),
            data=remove_course_data,
            format='json'
        )

        self.assertEqual(response.status_code, 204, response.data)
        self.assertFalse(
            CourseTaken.objects.filter(
                degree_profile=self.degree_profile, 
                course=self.cis_1600.id, 
                semester="2024A"
            ).exists()
        )


