import math
import uuid
from textwrap import dedent

import phonenumbers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import Case, Index, OuterRef, Q, Subquery, When
from django.db.models.functions import Cast
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from review.annotations import review_averages


User = get_user_model()


def string_dict_to_html(dictionary):
    html = ["<table width=100%>"]
    for key, value in dictionary.items():
        html.append("<tr>")
        html.append('<td>"{0}"</td>'.format(key))
        html.append('<td>"{0}"</td>'.format(value))
        html.append("</tr>")
    html.append("</table>")
    return "".join(html)


"""
Core Course Models
==================

The Instructor, Course and Section models define the core course information
used in Alert and Plan.

The StatusUpdate model holds changes to the "status" field over time, recording how course
availability changes over time.
"""


class Instructor(models.Model):
    """
    An academic instructor at Penn, e.g. Swapneel Sheth.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    name = models.CharField(
        max_length=255, unique=True, db_index=True, help_text="The full name of the instructor."
    )
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="The instructor's Penn Labs Accounts User object.",
    )

    def __str__(self):
        return self.name


class Department(models.Model):
    """
    An academic department at Penn, such as the CIS (Computer and Information Sci) department.
    """

    code = models.CharField(
        max_length=8,
        unique=True,
        db_index=True,
        help_text="The department code, e.g. `CIS` for the CIS department.",
    )
    name = models.CharField(
        max_length=255,
        help_text=dedent(
            """
        The name of the department, e.g. 'Computer and Information Sci' for the CIS department.
        """
        ),
    )

    def __str__(self):
        return self.code


def sections_with_reviews(queryset):
    from review.views import reviewbit_filters_pcr, section_filters_pcr

    # ^ imported here to avoid circular imports
    # get all the reviews for instructors in the Section.instructors many-to-many
    instructors_subquery = Subquery(
        Instructor.objects.filter(section__id=OuterRef(OuterRef("id"))).values("id").order_by()
    )

    return review_averages(
        queryset,
        reviewbit_subfilters=(
            reviewbit_filters_pcr
            & Q(review__section__course__topic=OuterRef("course__topic"))
            & Q(review__instructor__in=instructors_subquery)
        ),
        section_subfilters=(
            section_filters_pcr
            & Q(course__topic=OuterRef("course__topic"))
            & Q(instructors__in=instructors_subquery)
        ),
        extra_metrics=False,
    ).order_by("code")


def course_reviews(queryset):
    from review.views import reviewbit_filters_pcr, section_filters_pcr

    # ^ imported here to avoid circular imports

    return review_averages(
        queryset,
        reviewbit_subfilters=(
            reviewbit_filters_pcr & Q(review__section__course__topic=OuterRef("topic"))
        ),
        section_subfilters=(section_filters_pcr & Q(course__topic=OuterRef("topic"))),
        extra_metrics=False,
    )


class CourseManager(models.Manager):
    def get_queryset(self):
        return course_reviews(super().get_queryset())


class Course(models.Model):
    """
    A course at Penn, e.g. CIS-120 (Programming Languages and Techniques I)
    """

    objects = models.Manager()
    with_reviews = CourseManager()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="courses",
        help_text=dedent(
            """
        The Department object to which the course belongs, e.g. the CIS Department object
        for CIS-120.
        """
        ),
    )
    code = models.CharField(
        max_length=8, db_index=True, help_text="The course code, e.g. `120` for CIS-120."
    )
    semester = models.CharField(
        max_length=5,
        db_index=True,
        help_text=dedent(
            """
        The semester of the course (of the form YYYYx where x is A [for spring],
        B [summer], or C [fall]), e.g. `2019C` for fall 2019.
        """
        ),
    )

    title = models.TextField(
        help_text=dedent(
            """
        The title of the course, e.g. 'Programming Languages and Techniques I' for CIS-120.
        """
        )
    )
    description = models.TextField(
        blank=True,
        help_text=dedent(
            """
        The description of the course, e.g. 'A fast-paced introduction to the fundamental concepts
        of programming... [etc.]' for CIS-120.
        """
        ),
    )

    full_code = models.CharField(
        max_length=16,
        blank=True,
        db_index=True,
        help_text="The dash-joined department and code of the course, e.g. `CIS-120` for CIS-120.",
    )

    prerequisites = models.TextField(
        blank=True,
        help_text="Text describing the prereqs for a course, e.g. 'CIS 120, 160' for CIS-121.",
    )

    topic = models.ForeignKey(
        "Topic",
        related_name="courses",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="The Topic of this course",
    )

    primary_listing = models.ForeignKey(
        "Course",
        related_name="listing_set",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=dedent(
            """
        The primary Course object with which this course is crosslisted (all crosslisted courses
        have a primary listing). The set of crosslisted courses to which this course belongs can
        thus be accessed with the related field listing_set on the primary_listing course.
        """
        ),
    )

    num_activities = models.IntegerField(
        default=0,
        help_text=dedent(
            """
            The number of distinct activities belonging to this course (precomputed for efficiency).
            Maintained by the registrar import / recomputestats script.
            """
        ),
    )

    class Meta:
        unique_together = (("department", "code", "semester"), ("full_code", "semester"))

    def __str__(self):
        return "%s %s" % (self.full_code, self.semester)

    def full_str(self):
        return f"{self.full_code} ({self.semester}): {self.title}\n{self.description}"

    @property
    def is_primary(self):
        """
        Returns True iff this is the primary course among its crosslistings.
        """
        return self.primary_listing is None or self.primary_listing.id == self.id

    @property
    def crosslistings(self):
        """
        A QuerySet (list on frontend) of the Course objects which are crosslisted with this
        course (not including this course).
        """
        if self.primary_listing is not None:
            return self.primary_listing.listing_set.exclude(id=self.id)
        else:
            return Course.objects.none()

    @property
    def requirements(self):
        """
        A QuerySet (list on frontend) of all the Requirement objects this course fulfills. Note that
        a course fulfills a requirement if and only if it is not in the requirement's
        overrides set (related name nonrequirements_set), and is in the requirement's
        courses set (related name requirement_set) or its department is in the requirement's
        departments set (related name requirements).
        """
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
        if not self.topic:
            with transaction.atomic():
                try:
                    self.topic = (
                        Topic.objects.select_related("most_recent")
                        .filter(courses__full_code=self.full_code)[:1]
                        .get()
                    )
                    if self.topic.most_recent.semester < self.semester:
                        self.topic.most_recent = self.primary_listing or self
                        self.topic.save()
                except Topic.DoesNotExist:
                    topic = Topic(most_recent=self.primary_listing or self)
                    topic.save()
                    self.topic = topic
                super().save()
                self.crosslistings.update(topic=self.topic)


class Topic(models.Model):
    """
    A grouping of courses of the same topic (to accomodate course code changes).
    """

    most_recent = models.ForeignKey(
        "Course",
        related_name="+",
        on_delete=models.PROTECT,
        help_text=dedent(
            """
        The most recent course (by semester) of this topic. The `most_recent` course should
        be the `primary_listing` if it has crosslistings. These invariants are maintained
        by the `Topic.merge_with`, `Topic.add_course`, `Topic.from_course`, and `Course.save`
        methods. Defer to using these methods rather than setting this field manually.
        You must change the corresponding `Topic` object's `most_recent` field before
        deleting a Course if it is the `most_recent` course (`on_delete=models.PROTECT`).
        """
        ),
    )

    branched_from = models.ForeignKey(
        "Topic",
        related_name="branched_to",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=dedent(
            """
        When relevant, the Topic from which this Topic was branched (this will likely only be
        useful for the spring 2022 NGSS course code changes, where some courses were split into
        multiple new courses of different topics).
        """
        ),
    )

    @staticmethod
    def from_course(course):
        """
        Creates a new topic from a given course.
        """
        if course.topic:
            return course.topic
        course.save()
        return course.topic

    def merge_with(self, topic):
        """
        Merges this topic with the specified topic. Returns the resulting topic.
        """
        with transaction.atomic():
            if (
                self.most_recent.semester == topic.most_recent.semester
                and self.most_recent.full_code != topic.most_recent.full_code
            ):
                raise ValueError(
                    "Cannot merge topics with most_recent courses in the same semester "
                    "but different full codes."
                )
            elif self.most_recent.semester >= topic.most_recent.semester:
                Course.objects.filter(topic=topic).update(topic=self)
                topic.delete()
                return self
            else:
                Course.objects.filter(topic=self).update(topic=topic)
                self.delete()
                return topic

    def add_course(self, course):
        """
        Adds the specified course to this topic.
        """
        with transaction.atomic():
            course = course.primary_listing or course
            if course.semester > self.most_recent.semester:
                self.most_recent = course
                self.save()
            course.topic = self
            course.save()
            course.crosslistings.update(topic=self)

    def __str__(self):
        return f"Topic {self.id} ({self.most_recent.full_code} most recently)"


class Restriction(models.Model):
    """
    A registration restriction, e.g. PDP (permission needed from department)
    """

    code = models.CharField(
        max_length=10,
        unique=True,
        help_text=dedent(
            """
        A registration restriction control code, for instance 'PDP' for CIS-121 (permission
        required from dept for registration). See [bit.ly/3eu17m2](https://bit.ly/3eu17m2)
        for all options.
        """
        ),
    )
    description = models.TextField(
        help_text=dedent(
            """
        The registration restriction description, e.g. 'Permission Needed From Department'
        for the PDP restriction (on CIS-121, for example). See
        [bit.ly/3eu17m2](https://bit.ly/3eu17m2) for all options.
        """
        )
    )

    @property
    def permit_required(self):
        """
        True if permission is required from the department for registration, false otherwise.
        """
        return "permission" in self.description.lower()

    def __str__(self):
        return f"{self.code} - {self.description}"


class SectionManager(models.Manager):
    def get_queryset(self):
        return sections_with_reviews(super().get_queryset()).distinct()


class Section(models.Model):
    """
    This model represents a section of a course at Penn, e.g. CIS-120-001 for the CIS-120 course.
    """

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
        indexes = [
            Index(
                Case(
                    When(
                        Q(capacity__isnull=False) & Q(capacity__gt=0),
                        then=(
                            Cast(
                                "registration_volume",
                                models.FloatField(),
                            )
                            / Cast("capacity", models.FloatField())
                        ),
                    ),
                    default=None,
                    output_field=models.FloatField(null=True, blank=True),
                ),
                name="raw_demand",
            ),
        ]

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    code = models.CharField(
        max_length=16,
        db_index=True,
        help_text="The section code, e.g. `001` for the section CIS-120-001.",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="sections",
        help_text=dedent(
            """
        The Course object to which this section belongs, e.g. the CIS-120 Course object for
        CIS-120-001.
        """
        ),
    )
    full_code = models.CharField(
        max_length=32,
        blank=True,
        db_index=True,
        help_text=dedent(
            """
        The full code of the section, in the form '{dept code}-{course code}-{section code}',
        e.g. `CIS-120-001` for the 001 section of CIS-120.
        """
        ),
    )

    status = models.CharField(
        max_length=4,
        choices=STATUS_CHOICES,
        db_index=True,
        help_text="The registration status of the section. Options and meanings: "
        + string_dict_to_html(dict(STATUS_CHOICES)),
    )

    capacity = models.IntegerField(
        default=0,
        help_text="The number of allowed registrations for this section, "
        "e.g. `220` for CIS-120-001 (2020A).",
    )
    activity = models.CharField(
        max_length=50,
        choices=ACTIVITY_CHOICES,
        db_index=True,
        help_text="The section activity, e.g. `LEC` for CIS-120-001 (2020A). Options and meanings: "
        + string_dict_to_html(dict(ACTIVITY_CHOICES)),
    )
    meeting_times = models.TextField(
        blank=True,
        help_text=dedent(
            """
        A JSON-stringified list of meeting times of the form
        `{days code} {start time} - {end time}`, e.g.
        `["MWF 09:00 AM - 10:00 AM","F 11:00 AM - 12:00 PM","T 05:00 PM - 06:00 PM"]` for
        PHYS-151-001 (2020A). Each letter of the days code is of the form M, T, W, R, F for each
        day of the work week, respectively (and multiple days are combined with concatenation).
        To access the Meeting objects for this section, the related field `meetings` can be used.
        """
        ),
    )
    num_meetings = models.IntegerField(
        default=0,
        help_text=dedent(
            """
            The number of meetings belonging to this section (precomputed for efficiency).
            Maintained by the registrar import / recomputestats script.
            """
        ),
    )

    instructors = models.ManyToManyField(
        Instructor, help_text="The Instructor object(s) of the instructor(s) teaching the section."
    )
    associated_sections = models.ManyToManyField(
        "Section",
        help_text=dedent(
            """
        A list of all sections associated with the Course which this section belongs to; e.g. for
        CIS-120-001, all of the lecture and recitation sections for CIS-120 (including CIS-120-001)
        in the same semester.
        """
        ),
    )
    restrictions = models.ManyToManyField(
        Restriction,
        related_name="sections",
        blank=True,
        help_text="All registration Restriction objects to which this section is subject.",
    )

    credits = models.DecimalField(
        max_digits=3,  # some course for 2019C is 14 CR...
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
        help_text="The number of credits this section is worth.",
    )

    registration_volume = models.PositiveIntegerField(
        default=0, help_text="The number of active PCA registrations watching this section."
    )  # For the set of PCA registrations for this section, use the related field `registrations`.

    def __str__(self):
        return "%s %s" % (self.full_code, self.course.semester)

    @property
    def semester(self):
        """
        The semester of the course (of the form YYYYx where x is A [for spring],
        B [summer], or C [fall]), e.g. `2019C` for fall 2019.
        """
        return self.course.semester

    @property
    def is_open(self):
        """
        True if self.status == "O", False otherwise
        """
        return self.status == "O"

    percent_open = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text=dedent(
            """
        If this section is from the current semester, this is the percentage (expressed as a
        decimal number between 0 and 1) of the period between the beginning of its
        add/drop period and its last status update that this section was open
        (or 0 if it has had no status updates strictly within its add/drop period).
        If this section is from a previous semester, this is the percentage of its
        whole add/drop period that it was open.
        """
        ),
    )

    @property
    def current_percent_open(self):
        """
        The percentage (expressed as a decimal number between 0 and 1) of the period between
        the beginning of its add/drop period and min[the current time, the end of its
        registration period] that this section was open. If this section's registration
        period hasn't started yet, this property is null (None in Python).
        """
        from courses.util import get_current_semester, get_or_create_add_drop_period

        # ^ imported here to avoid circular imports

        if self.semester == get_current_semester():
            add_drop = get_or_create_add_drop_period(self.semester)
            add_drop_start = add_drop.estimated_start
            add_drop_end = add_drop.estimated_end
            current_time = timezone.now()
            if current_time <= add_drop_start:
                return None
            try:
                last_status_update = StatusUpdate.objects.filter(
                    section=self, created_at__gt=add_drop_start, created_at__lt=add_drop_end
                ).latest("created_at")
            except StatusUpdate.DoesNotExist:
                last_status_update = None
            last_update_dt = last_status_update.created_at if last_status_update else add_drop_start
            period_seconds = float(
                (min(current_time, add_drop_end) - add_drop_start).total_seconds()
            )
            percent_after_update = (
                float(self.is_open)
                * float((current_time - last_update_dt).total_seconds())
                / period_seconds
            )
            if last_status_update is None:
                return percent_after_update
            percent_before_update = (
                float(self.percent_open)
                * float((last_update_dt - add_drop_start).total_seconds())
                / period_seconds
            )
            return percent_before_update + percent_after_update
        else:
            return self.percent_open

    @property
    def raw_demand(self):
        """
        The current raw PCA demand of the section, which is defined as:
        [the number of active PCA registrations for this section]/[the class capacity]
        NOTE: if this section has a null or non-positive capacity, then this property will be null.
        """
        # Note for backend developers: this is a property, not a field. However,
        # in the Meta class for this model, we define the raw_property index identically to
        # this property's computation. Thus, you can access this value (as an indexed column)
        # in database queries using the same name. This is useful for computing
        # distribution estimates.
        if self.capacity is None or self.capacity <= 0:
            return None
        else:
            return float(self.registration_volume) / float(self.capacity)

    @property
    def last_status_update(self):
        """
        Returns the last StatusUpdate object for this section, or None if no status updates
        have occured for this section yet.
        """
        try:
            return StatusUpdate.objects.filter(section=self).latest("created_at")
        except StatusUpdate.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        self.full_code = f"{self.course.full_code}-{self.code}"
        super().save(*args, **kwargs)


class StatusUpdate(models.Model):
    """
    A registration status update for a specific section (e.g. CIS-120-001 went from open to close)
    """

    STATUS_CHOICES = (("O", "Open"), ("C", "Closed"), ("X", "Cancelled"), ("", "Unlisted"))
    section = models.ForeignKey(
        Section,
        related_name="status_updates",
        on_delete=models.CASCADE,
        help_text="The section which this status update applies to.",
    )
    old_status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        help_text="The old status code (from which the section changed). Options and meanings: "
        + string_dict_to_html(dict(STATUS_CHOICES)),
    )
    new_status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        help_text="The new status code (to which the section changed). Options and meanings: "
        + string_dict_to_html(dict(STATUS_CHOICES)),
    )
    created_at = models.DateTimeField(default=timezone.now)
    alert_sent = models.BooleanField(
        help_text="Was an alert was sent to a User as a result of this status update?"
    )
    # ^^^ alert_sent is true iff alert_for_course was called in accept_webhook in alert/views.py
    request_body = models.TextField()

    percent_through_add_drop_period = models.FloatField(
        null=True,
        blank=True,
        help_text="The percentage through the add/drop period at which this status update occurred."
        "This percentage is constrained within the range [0,1].",
    )  # This field is maintained in the save() method of alerts.models.AddDropPeriod,
    # and the save() method of StatusUpdate

    in_add_drop_period = models.BooleanField(
        default=False, help_text="Was this status update created during the add/drop period?"
    )  # This field is maintained in the save() method of alerts.models.AddDropPeriod,
    # and the save() method of StatusUpdate

    def __str__(self):
        d = dict(self.STATUS_CHOICES)
        return (
            f"{str(self.section)} - {d[self.old_status]} to {d[self.new_status]} "
            f"@ {str(self.created_at)}"
        )

    def save(self, *args, **kwargs):
        """
        This overridden save method first gets the add/drop period object for the semester of this
        StatusUpdate object (either by using the get_or_create_add_drop_period method or by using
        a passed-in add_drop_period kwarg, which can be used for efficiency in bulk operations
        over many StatusUpdate objects). Then it calls the overridden save method, and after that
        it sets the percent_through_add_drop_period field.
        """
        from alert.models import validate_add_drop_semester
        from courses.util import get_or_create_add_drop_period

        # ^ imported here to avoid circular imports

        add_drop_period = None
        if "add_drop_period" in kwargs:
            add_drop_period = kwargs["add_drop_period"]
            del kwargs["add_drop_period"]

        super().save(*args, **kwargs)

        # If this is a valid add/drop semester, set the percent_through_add_drop_period field
        try:
            validate_add_drop_semester(self.section.semester)
        except ValidationError:
            return

        if add_drop_period is None:
            add_drop_period = get_or_create_add_drop_period(self.section.semester)

        created_at = self.created_at
        start = add_drop_period.estimated_start
        end = add_drop_period.estimated_end
        if created_at < start:
            self.in_add_drop_period = False
            self.percent_through_add_drop_period = 0
        elif created_at > end:
            self.in_add_drop_period = False
            self.percent_through_add_drop_period = 1
        else:
            self.in_add_drop_period = True
            self.percent_through_add_drop_period = (created_at - start) / (end - start)
        super().save()


"""
Schedule Models
===============

The next section of models store information related to scheduling and location.
"""


class Building(models.Model):
    """A building at Penn."""

    code = models.CharField(
        max_length=4,
        unique=True,
        help_text=dedent(
            """
        The building code, for instance 570 for the Towne Building. To find the building code
        of a certain building, visit the [Penn Facilities Website](https://bit.ly/2BfE2FE).
        """
        ),
    )
    name = models.CharField(
        max_length=80,
        blank=True,
        help_text=dedent(
            """
        The name of the building, for instance 'Towne Building' for the Towne Building. For a
        list of building names, visit the [Penn Facilities Website](https://bit.ly/2BfE2FE).
        """
        ),
    )
    latitude = models.FloatField(
        blank=True,
        null=True,
        help_text=dedent(
            """
        The latitude of the building, in the signed decimal degrees format (global range of
        [-90.0, 90.0]), e.g. `39.961380` for the Towne Building.
        """
        ),
    )
    longitude = models.FloatField(
        blank=True,
        null=True,
        help_text=dedent(
            """
        The longitude of the building, in the signed decimal degrees format (global range of
        [-180.0, 180.0]), e.g. `-75.176773` for the Towne Building.
        """
        ),
    )

    def __str__(self):
        return self.name if len(self.name) > 0 else self.code


class Room(models.Model):
    """A room in a Building. It optionally may be named."""

    building = models.ForeignKey(
        Building,
        on_delete=models.CASCADE,
        help_text=dedent(
            """
        The Building object in which the room is located, e.g. the Levine Hall Building
        object for Wu and Chen Auditorium (rm 101).
        """
        ),
    )
    number = models.CharField(
        max_length=5, help_text="The room number, e.g. `101` for Wu and Chen Auditorium in Levine."
    )
    name = models.CharField(
        max_length=80,
        help_text="The room name (optional, empty string if none), e.g. 'Wu and Chen Auditorium'.",
    )

    class Meta:
        """To hold uniqueness constraint"""

        unique_together = (("building", "number"),)

    def __str__(self):
        return f"{self.building.code} {self.number}"


class Meeting(models.Model):
    """
    A single meeting of a section (a continuous span of time during which a section would meet).
    Note that a section which meets MWF 10:00 AM - 11:00 AM would have 3 associated meetings,
    10:00 AM - 11:00 AM on M, W, and F, respectively.
    """

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="meetings",
        help_text="The Section object to which this class meeting belongs.",
    )
    day = models.CharField(
        max_length=1,
        help_text="The single day on which the meeting takes place (one of M, T, W, R, or F).",
    )
    start = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="The start time of the meeting; hh:mm is formatted as hh.mm = h+mm/100.",
    )
    end = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="The end time of the meeting; hh:mm is formatted as hh.mm = h+mm/100.",
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        help_text="The Room object in which the meeting is taking place.",
    )

    class Meta:
        unique_together = (("section", "day", "start", "end", "room"),)

    @staticmethod
    def int_to_time(time):
        hour = math.floor(time) % 12
        minute = math.floor((time % 1) * 100)

        return f'{hour if hour != 0 else 12}:{str(minute).zfill(2)} {"AM" if time < 12 else "PM"}'

    @property
    def start_time(self):
        """
        The start time of the meeting, in the form hour:mm AM/PM, e.g. 10:00 AM or 1:30 PM
        (hour is not 0 padded but minute is).
        """
        return Meeting.int_to_time(self.start)

    @property
    def end_time(self):
        """
        The end time of the meeting, in the form hour:mm AM/PM, e.g. 10:00 AM or 1:30 PM
        (hour is not 0 padded but minute is).
        """
        return Meeting.int_to_time(self.end)

    @property
    def no_conflict_query(self):
        """
        Returns a Q() object representing the condition that another Meeting object
        does not overlap with this meeting object in day/time.
        """
        return ~Q(day=self.day) | Q(end__lte=self.start) | Q(start__gte=self.end)

    def __str__(self):
        return f"{self.section}: {self.day} {self.start_time}-{self.end_time} in {self.room}"


"""
Requirements
"""


class Requirement(models.Model):
    """
    An academic requirement which the specified course(s) fulfill(s). Not to be confused with
    Restriction objects, which are restrictions on registration for certain course section(s).
    """

    SCHOOL_CHOICES = (("SEAS", "Engineering"), ("WH", "Wharton"), ("SAS", "College"))
    semester = models.CharField(
        max_length=5,
        db_index=True,
        help_text=dedent(
            """
        The semester of the requirement (of the form YYYYx where x is A [for spring], B [summer],
        or C [fall]), e.g. `2019C` for fall 2019. We organize requirements by semester so that we
        don't get huge related sets which don't give particularly good info.
        """
        ),
    )
    school = models.CharField(
        max_length=5,
        choices=SCHOOL_CHOICES,
        db_index=True,
        help_text=dedent(
            """
        What school this requirement belongs to, e.g. `SAS` for the SAS 'Formal Reasoning Course'
        requirement satisfied by CIS-120. Options and meanings:
        """
            + string_dict_to_html(dict(SCHOOL_CHOICES))
        ),
    )
    code = models.CharField(
        max_length=10,
        db_index=True,
        help_text=dedent(
            """
        The code identifying this requirement, e.g. `MFR` for 'Formal Reasoning Course',
        an SAS requirement satisfied by CIS-120.
        """
        ),
    )
    name = models.CharField(
        max_length=255,
        help_text=dedent(
            """
        The name of the requirement, e.g. 'Formal Reasoning Course', an SAS requirement
        satisfied by CIS-120.
        """
        ),
    )

    requirement_conditions = dedent(
        """
        Note that a course satisfies a requirement if and only if it is not in the
        overrides set, and it is either in the courses set or its department is in the departments
        set.
        """
    )
    departments = models.ManyToManyField(
        Department,
        related_name="requirements",
        blank=True,
        help_text=dedent(
            """
        All the Department objects for which any course in that department
        (if not in overrides) would satisfy this requirement. Usually if a whole department
        satisfies a requirement, individual courses from that department will not be added to
        the courses set. Also, to specify specific courses which do not satisfy the requirement
        (even if their department is in the departments set), the overrides set is used.
        For example, CIS classes count as engineering (ENG) courses, but CIS-125 is NOT an
        engineering class, so for the ENG requirement, CIS-125 would be in the overrides
        set even though the CIS Department object would be in the departments set.
        """
            + requirement_conditions
        ),
    )
    courses = models.ManyToManyField(
        Course,
        related_name="requirement_set",
        blank=True,
        help_text=dedent(
            """
        Individual Course objects which satisfy this requirement (not necessarily
        comprehensive, as often entire departments will satisfy the requirement, but not
        every course in the department will necessarily be added to this set). For example,
        CIS 398 would be in the courses set for the NATSCI engineering requirement, since
        it is the only CIS class that satisfies that requirement.
        """
            + requirement_conditions
        ),
    )
    overrides = models.ManyToManyField(
        Course,
        related_name="nonrequirement_set",
        blank=True,
        help_text=dedent(
            """
        Individual Course objects which do not satisfy this requirement. This set
        is usually used to add exceptions to departments which satisfy requirements.
        For example, CIS classes count as engineering (ENG) courses, but CIS-125 is NOT an
        engineering class, so for the ENG requirement, CIS-125 would be in the overrides
        set even though the CIS Department would be in the departments set.
        """
            + requirement_conditions
        ),
    )

    class Meta:
        unique_together = (("semester", "code", "school"),)

    def __str__(self):
        return f"{self.code} @ {self.school} - {self.semester}"

    @property
    def satisfying_courses(self):
        """
        A QuerySet (list on frontend) of all Course objects which satisfy this requirement;
        in other words, a course satisfies this requirement if and only if it is in this
        set.  A course is in this set if and only if it is not in the overrides set,
        and it is either in the courses set or its department is in the departments set.
        """
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
    Describes a type of access privilege that an API key can have.
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

    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="profile",
        help_text="The User object to which this User Profile object belongs.",
    )
    email = models.EmailField(
        blank=True, null=True, help_text="The email of the User. Defaults to null."
    )
    push_notifications = models.BooleanField(
        default=False,
        help_text=dedent(
            """
        Defaults to False, changed to True if the User enables mobile push notifications
        for PCA, rather than text notifications.
        """
        ),
    )
    # phone field defined underneath validate_phone function below

    def validate_phone(value):
        """
        Validator to check that a phone number is in the proper form. The number must be in a
        form which is parseable by the
        [phonenumbers library](https://pypi.org/project/phonenumbers/).
        """
        if value.strip() == "":
            return
        try:
            phonenumbers.parse(value, "US")
        except phonenumbers.phonenumberutil.NumberParseException:
            raise ValidationError("Enter a valid phone number.")

    phone = models.CharField(
        blank=True,
        null=True,
        max_length=100,
        validators=[validate_phone],
        help_text=dedent(
            """
        The phone number of the user. Defaults to null.
        The phone number will be stored in the E164 format, but any form parseable by the
        [phonenumbers library](https://pypi.org/project/phonenumbers/)
        will be accepted and converted to E164 format automatically upon saving.
        """
        ),
    )

    def __str__(self):
        return "Data from User: %s" % self.user

    def save(self, *args, **kwargs):
        """
        This save method converts the phone field to the E164 format, unless the number is in a
        form unparseable by the [phonenumbers library](https://pypi.org/project/phonenumbers/),
        in which case it sets it throws an error (this case should have been caught
        already in the view logic, but it is left in for redundancy).  However, if the
        phone number is simply an empty string or only spaces, it is set to None and
        does not throw an error.
        It then calls the normal save method.
        """
        if self.phone is not None and self.phone.strip() == "":
            self.phone = None
        if self.phone is not None:
            try:
                phone_number = phonenumbers.parse(self.phone, "US")
                self.phone = phonenumbers.format_number(
                    phone_number, phonenumbers.PhoneNumberFormat.E164
                )
            except phonenumbers.phonenumberutil.NumberParseException:
                raise ValidationError("Invalid phone number (this should have been caught already)")
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    This post_save hook triggers automatically when a User object is saved, and if no UserProfile
    object exists for that User, it will create one and set its email field to the User's email
    field (if that field is nonempty).
    """
    _, created = UserProfile.objects.get_or_create(user=instance)
    if created and instance.email != "":
        instance.profile.email = instance.email
    instance.profile.save()
