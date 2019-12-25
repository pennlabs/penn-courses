import math
import uuid

import phonenumbers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from options.models import get_value
from plan.annotations import course_reviews, sections_with_reviews


def get_current_semester():
    return get_value('SEMESTER', '2019C')


"""
Core Course Models
==================

The Instructor, Course and Section models define the core course information
used in Alert and Plan.

The StatusUpdate model holds changes to the "status" field over time, recording how course availability changes
over time.
"""


class Instructor(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255, unique=True, db_index=True)

    def __str__(self):
        return self.name


class Department(models.Model):
    code = models.CharField(max_length=8, unique=True, db_index=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.code


class CourseManager(models.Manager):
    def get_queryset(self):
        return course_reviews(super().get_queryset())


class Course(models.Model):
    objects = models.Manager()
    with_reviews = CourseManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    code = models.CharField(max_length=8)
    semester = models.CharField(max_length=5, db_index=True)

    title = models.TextField()
    description = models.TextField(blank=True)

    full_code = models.CharField(max_length=16, blank=True, db_index=True)

    prerequisites = models.TextField(blank=True)

    # Handle crosslisted courses.
    # All crosslisted courses have a "primary listing" in the registrar.
    primary_listing = models.ForeignKey('Course',
                                        related_name='listing_set',
                                        on_delete=models.CASCADE,
                                        null=True,
                                        blank=True)

    class Meta:
        unique_together = (('department', 'code', 'semester'), ('full_code', 'semester'))

    def __str__(self):
        return '%s %s' % (self.course_id, self.semester)

    @property
    def course_id(self):
        return '%s-%s' % (self.department, self.code)

    @property
    def crosslistings(self):
        if self.primary_listing is not None:
            return self.primary_listing.listing_set.exclude(id=self.id)
        else:
            return None

    @property
    def requirements(self):
        return Requirement.objects.exclude(id__in=self.nonrequirement_set.all())\
            .filter(semester=self.semester)\
            .filter(Q(id__in=self.requirement_set.all()) | Q(id__in=self.department.requirements.all()))

    def save(self, *args, **kwargs):
        self.full_code = f'{self.department.code}-{self.code}'
        super().save(*args, **kwargs)


class Restriction(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField()

    @property
    def permit_required(self):
        return 'permission' in self.description.lower()

    def __str__(self):
        return f'{self.code} - {self.description}'


class SectionManager(models.Manager):
    def get_queryset(self):
        return sections_with_reviews(super().get_queryset()).distinct()


class Section(models.Model):
    objects = models.Manager()
    with_reviews = SectionManager()

    STATUS_CHOICES = (
        ('O', 'Open'),
        ('C', 'Closed'),
        ('X', 'Cancelled'),
        ('', 'Unlisted'),
    )

    ACTIVITY_CHOICES = (
        ('CLN', 'Clinic'),
        ('DIS', 'Dissertation'),
        ('IND', 'Independent Study'),
        ('LAB', 'Lab'),
        ('LEC', 'Lecture'),
        ('MST', 'Masters Thesis'),
        ('REC', 'Recitation'),
        ('SEM', 'Seminar'),
        ('SRT', 'Senior Thesis'),
        ('STU', 'Studio'),
        ('***', 'Undefined'),
    )

    class Meta:
        unique_together = (('code', 'course'), )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    code = models.CharField(max_length=16)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sections')
    full_code = models.CharField(max_length=32, blank=True, db_index=True)

    status = models.CharField(max_length=4, choices=STATUS_CHOICES, db_index=True)

    capacity = models.IntegerField(default=0)
    activity = models.CharField(max_length=50, choices=ACTIVITY_CHOICES, db_index=True)
    meeting_times = models.TextField(blank=True)

    instructors = models.ManyToManyField(Instructor)
    associated_sections = models.ManyToManyField('Section')
    restrictions = models.ManyToManyField(Restriction, blank=True)

    credits = models.DecimalField(max_digits=3,  # some course for 2019C is 14 CR...
                                  decimal_places=2,
                                  null=True,
                                  blank=True,
                                  db_index=True)

    def __str__(self):
        return '%s-%s %s' % (self.course.course_id, self.code, self.course.semester)

    @property
    def normalized(self):
        """String used for querying updates to this section with the Penn API"""
        return '%s-%s' % (self.course.course_id, self.code)

    @property
    def semester(self):
        return self.course.semester

    @property
    def is_open(self):
        return self.status == 'O'

    def save(self, *args, **kwargs):
        self.full_code = f'{self.course.full_code}-{self.code}'
        super().save(*args, **kwargs)


class StatusUpdate(models.Model):
    STATUS_CHOICES = (
        ('O', 'Open'),
        ('C', 'Closed'),
        ('X', 'Cancelled'),
        ('', 'Unlisted')
    )
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    old_status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    new_status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    alert_sent = models.BooleanField()
    request_body = models.TextField()

    def __str__(self):
        d = dict(self.STATUS_CHOICES)
        return f'{self.section.__str__()} - {d[self.old_status]} to {d[self.new_status]}'


"""
Schedule Models
===============

The next section of models store information related to scheduling and location.
"""


class Building(models.Model):
    """ A building at Penn. """
    code = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=80, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return self.name if len(self.name) > 0 else self.code


class Room(models.Model):
    """ A room in a Building. It optionally may be named. """
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    number = models.CharField(max_length=5)
    name = models.CharField(max_length=80)

    class Meta:
        """ To hold uniqueness constraint """
        unique_together = (('building', 'number'),)

    def __str__(self):
        return f'{self.building.code} {self.number}'


class Meeting(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='meetings')
    day = models.CharField(max_length=1)
    # the time hh:mm is formatted as decimal hh.mm, h + mm / 100
    start = models.DecimalField(max_digits=4,
                                decimal_places=2)
    end = models.DecimalField(max_digits=4,
                              decimal_places=2)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('section', 'day', 'start', 'end', 'room'), )

    @staticmethod
    def int_to_time(time):
        hour = math.floor(time) % 12
        minute = (time % 1) * 60

        return f'{hour if hour != 0 else 12}:{minute if minute != 0 else "00"} {"AM" if time < 12 else "PM"}'

    @property
    def start_time(self):
        return Meeting.int_to_time(self.start)

    @property
    def end_time(self):
        return Meeting.int_to_time(self.end)

    def __str__(self):
        return f'{self.section}: {self.start_time}-{self.end_time} in {self.room}'


"""
Requirements
"""


class Requirement(models.Model):
    SCHOOL_CHOICES = (
        ('SEAS', 'Engineering'),
        ('WH', 'Wharton'),
        ('SAS', 'College')
    )
    # organize requirements by semester so that we don't get huge related sets which don't give particularly good
    # info.
    semester = models.CharField(max_length=5, db_index=True)
    # what school this requirement belongs to
    school = models.CharField(max_length=5, choices=SCHOOL_CHOICES, db_index=True)
    # code identifying this requirement
    code = models.CharField(max_length=10, db_index=True)
    # name of the requirement
    name = models.CharField(max_length=255)

    # Departments which satisfy this requirement
    departments = models.ManyToManyField(Department, related_name='requirements', blank=True)
    # Courses which satisfy this requirement
    courses = models.ManyToManyField(Course, related_name='requirement_set', blank=True)

    # Courses which do not satisfy this requirement.
    # For example, CIS classes are Engineering courses, but CIS-125 is NOT an engineering class, so for the ENG
    # requirement, CIS-125 would go into the overrides set.
    overrides = models.ManyToManyField(Course, related_name='nonrequirement_set', blank=True)

    class Meta:
        unique_together = (('semester', 'code', 'school'), )

    def __str__(self):
        return f'{self.code} @ {self.school} - {self.semester}'

    @property
    def satisfying_courses(self):
        return Course.objects.all()\
            .exclude(id__in=self.overrides.all())\
            .filter(Q(department__in=self.departments.all(), semester=self.semester) | Q(id__in=self.courses.all()))


"""
3rd-Party API
"""

PCA_REGISTRATION = 'PCA_REGISTRATION'


class APIPrivilege(models.Model):
    """
    Describes a type of access privelege that an API key can have.
    """
    code = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)


class APIKey(models.Model):
    """
    An API Key is linked with an email address for contact purposes. May link with a user @ Penn if we wanted to
    restrict that.
    """
    email = models.EmailField()
    code = models.CharField(max_length=100, blank=True, unique=True, default=uuid.uuid4)
    active = models.BooleanField(blank=True, default=True)

    privileges = models.ManyToManyField(APIPrivilege, related_name='key_set', blank=True)


class UserData(models.Model):
    """
    A model that stores all user data from PCX users
    """
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='user')
    email = models.EmailField(blank=True, null=True)

    def validate_phone(value):
        try:
            phonenumbers.parse(value, 'US')
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValidationError('Enter a valid phone number.')

    phone = models.CharField(blank=True, null=True, max_length=100, validators=[validate_phone])

    def __str__(self):
        return 'Data from User: %s' % self.user

    def save(self, *args, **kwargs):
        if self.phone is not None:
            try:
                phone_number = phonenumbers.parse(self.phone, 'US')
                self.phone = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
            except phonenumbers.phonenumberutil.NumberParseException:
                raise ValidationError('Invalid phone number (this should have been caught already)')
        super(UserData, self).save(*args, **kwargs)
