from django.test import TestCase
from rest_framework.test import APIClient

from degree.models import Degree, Rule


class DegreeListTest(TestCase):
    def test_list_degrees(self):
        pass


class DegreeDetailTest(TestCase):
    def test_retrieve_degree_detail(self):
        pass

    def test_retrieve_degree_detail_invalid_id(self):
        pass


class UserDegreePlanViewsetTest(TestCase):
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
