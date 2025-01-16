# from django.test import TestCase
# from django.contrib.auth import get_user_model
# from django.core.management import call_command

# from plan.models import Schedule, NumberCalenders
# from courses.models import Section, Course, Department
# from courses.util import get_current_semester

# User = get_user_model()

# class CountSchedulesTest(TestCase):
#     def setUp(self):
#         # Set the current semester for testing purposes
#         self.semester = get_current_semester()

#         # Create a department
#         self.department = Department.objects.create(
#             code='CIS',
#             name='Computer and Information Science'
#         )

#         # Create a course in the current semester
#         self.course = Course.objects.create(
#             department=self.department,
#             code='120',
#             semester=self.semester,
#             title='Programming Languages and Techniques I'
#         )

#         # Create two sections for the course
#         self.section1 = Section.objects.create(
#             code='001',
#             course=self.course
#         )
#         self.section2 = Section.objects.create(
#             code='002',
#             course=self.course
#         )

#         # Create three users
#         self.user1 = User.objects.create_user(username='user1', password='pass')
#         self.user2 = User.objects.create_user(username='user2', password='pass')
#         self.user3 = User.objects.create_user(username='user3', password='pass')

#         # Create schedules for the users
#         # User1 has section1
#         self.schedule1 = Schedule.objects.create(
#             person=self.user1,
#             semester=self.semester,
#             name='User1 Schedule'
#         )
#         self.schedule1.sections.add(self.section1)

#         # User2 has section1 and section2
#         self.schedule2 = Schedule.objects.create(
#             person=self.user2,
#             semester=self.semester,
#             name='User2 Schedule'
#         )
#         self.schedule2.sections.add(self.section1, self.section2)

#         # User3 has section2
#         self.schedule3 = Schedule.objects.create(
#             person=self.user3,
#             semester=self.semester,
#             name='User3 Schedule'
#         )
#         self.schedule3.sections.add(self.section2)

#     def test_countschedules_command(self):
#         # Run the countschedules command
#         call_command('countschedules')

#         # Fetch the NumberCalenders instances for each section
#         nc_section1 = NumberCalenders.objects.get(
#             section=self.section1,
#             semester=self.semester
#         )
#         nc_section2 = NumberCalenders.objects.get(
#             section=self.section2,
#             semester=self.semester
#         )

#         # Check that the counts are correct
#         # Section1 is in schedules of user1 and user2 (total 2 unique users)
#         self.assertEqual(nc_section1.count, 2)

#         # Section2 is in schedules of user2 and user3 (total 2 unique users)
#         self.assertEqual(nc_section2.count, 2)

#         # Optionally, check that there are only two NumberCalenders entries
#         total_nc_entries = NumberCalenders.objects.filter(semester=self.semester).count()
#         self.assertEqual(total_nc_entries, 2)
