import math
import uuid

import phonenumbers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Avg, FloatField, OuterRef, Q, Subquery
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from options.models import get_value

from review.models import ReviewBit


def get_current_semester():
    return get_value("SEMESTER", "2019C")


"""
Core Course Models
==================

The Instructor, Course and Section models define the core course information
used in Alert and Plan.

The StatusUpdate model holds changes to the "status" field over time, recording how course
availability changes over time.
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


"""
Queryset annotations
====================

This file has code which annotates Course and Section querysets with Review information.
There's some tricky JOINs going on here, through the Subquery objects which you can
read about here:
https://docs.djangoproject.com/en/2.2/ref/models/expressions/#subquery-expressions.

This allows us to have the database do all of the work of averaging PCR data, so that we can get
all of our Course and Section data in two queries.
"""


# Annotations are basically the same for Course and Section, save a few of the subfilters,
# so generalize it out.
def review_averages(queryset, subfilters):
    """
    Annotate the queryset with the average of all reviews matching the subfilters.
    """
    fields = ["course_quality", "difficulty", "instructor_quality", "work_required"]
    return queryset.annotate(
        **{
            field: Subquery(
                ReviewBit.objects.filter(field=field, **subfilters)
                .values("field")
                .order_by()
                .annotate(avg=Avg("score"))
                .values("avg")[:1],
                output_field=FloatField(),
            )
            for field in fields
        }
    )


def sections_with_reviews(queryset):
    return review_averages(
        queryset,
        {
            "review__section__course__full_code": OuterRef("course__full_code"),
            # get all the reviews for instructors in the Section.instructors many-to-many
            "review__instructor__in": Subquery(
                Instructor.objects.filter(section=OuterRef(OuterRef("pk"))).values("pk").order_by()
            ),
        },
    ).order_by("code")


def course_reviews(queryset):
    return review_averages(queryset, {"review__section__course__full_code": OuterRef("full_code")})


class CourseManager(models.Manager):
    def get_queryset(self):
        return course_reviews(super().get_queryset())


class Course(models.Model):
    objects = models.Manager()
    with_reviews = CourseManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="courses")
    code = models.CharField(max_length=8)
    semester = models.CharField(max_length=5, db_index=True)

    title = models.TextField()
    description = models.TextField(blank=True)

    full_code = models.CharField(max_length=16, blank=True, db_index=True)

    prerequisites = models.TextField(blank=True)

    # Handle crosslisted courses.
    # All crosslisted courses have a "primary listing" in the registrar.
    primary_listing = models.ForeignKey(
        "Course", related_name="listing_set", on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        unique_together = (("department", "code", "semester"), ("full_code", "semester"))

    def __str__(self):
        return "%s %s" % (self.full_code, self.semester)

    @property
    def crosslistings(self):
        if self.primary_listing is not None:
            return self.primary_listing.listing_set.exclude(id=self.id)
        else:
            return None

    @property
    def requirements(self):
        return (
            Requirement.objects.exclude(id__in=self.nonrequirement_set.all())
            .filter(semester=self.semester)
            .filter(
                Q(id__in=self.requirement_set.all()) | Q(id__in=self.department.requirements.all())
            )
        )

    def save(self, *args, **kwargs):
        self.full_code = f"{self.department.code}-{self.code}"
        super().save(*args, **kwargs)


class Restriction(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField()

    @property
    def permit_required(self):
        return "permission" in self.description.lower()

    def __str__(self):
        return f"{self.code} - {self.description}"


class SectionManager(models.Manager):
    def get_queryset(self):
        return sections_with_reviews(super().get_queryset()).distinct()


class Section(models.Model):
    objects = models.Manager()
    with_reviews = SectionManager()

    STATUS_CHOICES = (
        ("O", "Open"),
        ("C", "Closed"),
        ("X", "Cancelled"),
        ("", "Unlisted"),
    )

    ACTIVITY_CHOICES = (
        ("CLN", "Clinic"),
        ("DIS", "Dissertation"),
        ("IND", "Independent Study"),
        ("LAB", "Lab"),
        ("LEC", "Lecture"),
        ("MST", "Masters Thesis"),
        ("REC", "Recitation"),
        ("SEM", "Seminar"),
        ("SRT", "Senior Thesis"),
        ("STU", "Studio"),
        ("***", "Undefined"),
    )

    class Meta:
        unique_together = (("code", "course"),)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    code = models.CharField(max_length=16)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sections")
    full_code = models.CharField(max_length=32, blank=True, db_index=True)

    status = models.CharField(max_length=4, choices=STATUS_CHOICES, db_index=True)

    capacity = models.IntegerField(default=0)
    activity = models.CharField(max_length=50, choices=ACTIVITY_CHOICES, db_index=True)
    meeting_times = models.TextField(blank=True)

    instructors = models.ManyToManyField(Instructor)
    associated_sections = models.ManyToManyField("Section")
    restrictions = models.ManyToManyField(Restriction, blank=True)

    credits = models.DecimalField(
        max_digits=3,  # some course for 2019C is 14 CR...
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
    )

    def __str__(self):
        return "%s %s" % (self.full_code, self.course.semester)

    @property
    def semester(self):
        return self.course.semester

    @property
    def is_open(self):
        return self.status == "O"

    def save(self, *args, **kwargs):
        self.full_code = f"{self.course.full_code}-{self.code}"
        super().save(*args, **kwargs)


class StatusUpdate(models.Model):
    STATUS_CHOICES = (("O", "Open"), ("C", "Closed"), ("X", "Cancelled"), ("", "Unlisted"))
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    old_status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    new_status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    alert_sent = models.BooleanField()
    # ^^^ alert_sent is true iff alert_for_course was called in accept_webhook in alert/views.py
    # equivalently, iff SEND_FROM_WEBHOOK == True and SEMESTER == course_term, or the request
    # is otherwise invalid
    request_body = models.TextField()

    def __str__(self):
        d = dict(self.STATUS_CHOICES)
        return f"{self.section.__str__()} - {d[self.old_status]} to {d[self.new_status]}"


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

        unique_together = (("building", "number"),)

    def __str__(self):
        return f"{self.building.code} {self.number}"


class Meeting(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="meetings")
    day = models.CharField(max_length=1)
    # the time hh:mm is formatted as decimal hh.mm, h + mm / 100
    start = models.DecimalField(max_digits=4, decimal_places=2)
    end = models.DecimalField(max_digits=4, decimal_places=2)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("section", "day", "start", "end", "room"),)

    @staticmethod
    def int_to_time(time):
        hour = math.floor(time) % 12
        minute = (time % 1) * 60

        return f'{hour if hour != 0 else 12}:{minute if minute != 0 else "00"} {"AM" if time < 12 else "PM"}'  # noqa: E501

    @property
    def start_time(self):
        return Meeting.int_to_time(self.start)

    @property
    def end_time(self):
        return Meeting.int_to_time(self.end)

    def __str__(self):
        return f"{self.section}: {self.start_time}-{self.end_time} in {self.room}"


"""
Requirements
"""


class Requirement(models.Model):
    SCHOOL_CHOICES = (("SEAS", "Engineering"), ("WH", "Wharton"), ("SAS", "College"))
    # organize requirements by semester so that we don't get huge related sets which don't give
    # particularly good info.
    semester = models.CharField(max_length=5, db_index=True)
    # what school this requirement belongs to
    school = models.CharField(max_length=5, choices=SCHOOL_CHOICES, db_index=True)
    # code identifying this requirement
    code = models.CharField(max_length=10, db_index=True)
    # name of the requirement
    name = models.CharField(max_length=255)

    # Departments which satisfy this requirement
    departments = models.ManyToManyField(Department, related_name="requirements", blank=True)
    # Courses which satisfy this requirement
    courses = models.ManyToManyField(Course, related_name="requirement_set", blank=True)

    # Courses which do not satisfy this requirement.
    # For example, CIS classes are Engineering courses, but CIS-125 is NOT an engineering class,
    # so for the ENG requirement, CIS-125 would go into the overrides set.
    overrides = models.ManyToManyField(Course, related_name="nonrequirement_set", blank=True)

    class Meta:
        unique_together = (("semester", "code", "school"),)

    def __str__(self):
        return f"{self.code} @ {self.school} - {self.semester}"

    @property
    def satisfying_courses(self):
        return (
            Course.objects.all()
            .exclude(id__in=self.overrides.all())
            .filter(
                Q(department__in=self.departments.all(), semester=self.semester)
                | Q(id__in=self.courses.all())
            )
        )


"""
3rd-Party API
"""

PCA_REGISTRATION = "PCA_REGISTRATION"


class APIPrivilege(models.Model):
    """
    Describes a type of access privelege that an API key can have.
    """

    code = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)


class APIKey(models.Model):
    """
    An API Key is linked with an email address for contact purposes. May link with a user @ Penn
    if we wanted to restrict that.
    """

    email = models.EmailField()
    code = models.CharField(max_length=100, blank=True, unique=True, default=uuid.uuid4)
    active = models.BooleanField(blank=True, default=True)

    privileges = models.ManyToManyField(APIPrivilege, related_name="key_set", blank=True)


class UserProfile(models.Model):
    """
    A model that stores all user data from PCX users
    """

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="profile")
    email = models.EmailField(blank=True, null=True)
    # phone field defined underneath validate_phone function below

    def validate_phone(value):
        try:
            phonenumbers.parse(value, "US")
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValidationError("Enter a valid phone number.")

    phone = models.CharField(blank=True, null=True, max_length=100, validators=[validate_phone])

    def __str__(self):
        return "Data from User: %s" % self.user

    def save(self, *args, **kwargs):
        if self.phone is not None:
            try:
                phone_number = phonenumbers.parse(self.phone, "US")
                self.phone = phonenumbers.format_number(
                    phone_number, phonenumbers.PhoneNumberFormat.E164
                )
            except phonenumbers.phonenumberutil.NumberParseException:
                raise ValidationError("Invalid phone number (this should have been caught already)")
        super(UserProfile, self).save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    UserProfile.objects.get_or_create(user=instance)
    instance.profile.save()
