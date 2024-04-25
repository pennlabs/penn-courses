import math
import uuid
from textwrap import dedent

import phonenumbers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models, transaction
from django.db.models import OuterRef, Q, Subquery
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from PennCourses.settings.base import FIRST_BANNER_SEM, PRE_NGSS_PERMIT_REQ_RESTRICTION_CODES
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
        max_length=255, db_index=True, help_text="The full name of the instructor."
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
    from review.views import section_filters_pcr

    # ^ imported here to avoid circular imports
    # get all the reviews for instructors in the Section.instructors many-to-many
    instructors_subquery = Subquery(
        Instructor.objects.filter(section__id=OuterRef(OuterRef("id"))).values("id")
    )

    return review_averages(
        queryset,
        reviewbit_subfilters=(
            Q(review__section__course__topic=OuterRef("course__topic"))
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
    from review.views import section_filters_pcr

    # ^ imported here to avoid circular imports

    return review_averages(
        queryset,
        reviewbit_subfilters=(Q(review__section__course__topic=OuterRef("topic"))),
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
        max_length=8,
        db_index=True,
        help_text="The course code, e.g. `120` for CIS-120.",
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

    syllabus_url = models.TextField(
        blank=True,
        null=True,
        help_text=dedent(
            """
            A URL for the syllabus of the course, if available.
            Not available for courses offered in or before spring 2022.
            """
        ),
    )

    full_code = models.CharField(
        max_length=16,
        blank=True,
        db_index=True,
        help_text="The dash-joined department and code of the course, e.g. `CIS-120` for CIS-120.",
    )

    credits = models.DecimalField(
        max_digits=4,  # some course for 2019C is 14 CR...
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
        help_text="The number of credits this course takes. This is precomputed for efficiency.",
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
        help_text="The Topic of this course (computed from the `parent_course` graph).",
    )

    parent_course = models.ForeignKey(
        "Course",
        related_name="children",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text=dedent(
            """
        The parent of this course (the most recent offering of this course in a previous semester).
        The graph of parent relationships is used to determine course topics. Any manual changes
        to this field should be denoted with `manually_set_parent_course=True`, so they are not
        overwritten by our automatic script.
        """
        ),
    )

    manually_set_parent_course = models.BooleanField(
        default=False,
        help_text=dedent(
            """
        A flag indicating whether the `parent_course` field of this course was confirmed/set
        manually or from a University-provided crosswalk,
        rather than inferred by an automatic script.
        """
        ),
    )

    primary_listing = models.ForeignKey(
        "Course",
        related_name="listing_set",
        on_delete=models.CASCADE,
        blank=True,  # So you can leave blank for a self-reference on course creation forms
        help_text=dedent(
            """
        The primary Course object with which this course is crosslisted. The set of crosslisted
        courses to which this course belongs can thus be accessed with the related field
        `listing_set` on the `primary_listing` course. If a course doesn't have any crosslistings,
        its `primary_listing` foreign key will point to itself. If you call `.save()` on a course
        without setting its `primary_listing` field, the overridden `Course.save()` method will
        automatically set its `primary_listing` to a self-reference.
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
        unique_together = (
            ("department", "code", "semester"),
            ("full_code", "semester"),
            ("topic", "semester"),
        )

    def __str__(self):
        return "%s %s" % (self.full_code, self.semester)

    def full_str(self):
        return f"{self.full_code} ({self.semester}): {self.title}\n{self.description}"

    @property
    def is_primary(self):
        """
        Returns True iff this is the primary course among its crosslistings.
        """
        return self.primary_listing.id == self.id

    @property
    def from_new_banner_api(self):
        """
        This property is used to determine whether the course was imported from the new
        OpenData API based on Banner, the university's new course data management system
        (docs: https://app.swaggerhub.com/apis-docs/UPennISC/open-data/prod),
        as opposed to the old OpenData API
        (docs: https://esb.isc-seo.upenn.edu/8091/documentation).
        """
        return self.semester >= FIRST_BANNER_SEM

    @property
    def crosslistings(self):
        """
        A QuerySet (list on frontend) of the Course objects which are crosslisted with this
        course (not including this course).
        """
        return self.primary_listing.listing_set.exclude(id=self.id)

    @property
    def pre_ngss_requirements(self):
        """
        A QuerySet (list on frontend) of all the PreNGSSRequirement objects this course fulfills.
        Note that a course fulfills a requirement if and only if it is not in the requirement's
        overrides set (related name nonrequirements_set), and is in the requirement's
        courses set (related name requirement_set) or its department is in the requirement's
        departments set (related name requirements).
        """
        return (
            PreNGSSRequirement.objects.exclude(id__in=self.pre_ngss_nonrequirement_set.all())
            .filter(semester=self.semester)
            .filter(
                Q(id__in=self.pre_ngss_requirement_set.all())
                | Q(id__in=self.department.pre_ngss_requirements.all())
            )
        )

    def save(self, *args, **kwargs):
        """
        This overridden `.save()` method enforces the following invariants on the course:
          - The course's full code equals the dash-joined department and code
          - If a course doesn't have crosslistings, its `primary_listing` is a self-reference
        """
        from courses.util import get_set_id, is_fk_set  # avoid circular imports

        self.full_code = f"{self.department.code}-{self.code}"

        with transaction.atomic():
            # Set primary_listing to self if not set
            if not is_fk_set(self, "primary_listing"):
                self.primary_listing_id = self.id or get_set_id(self)

            super().save(*args, **kwargs)


class Topic(models.Model):
    """
    A grouping of courses of the same topic (to accomodate course code changes).
    Topics are SOFT STATE, meaning they are not the source of truth for course groupings.
    They are recomputed nightly from the `parent_course` graph
    (in the recompute_soft_state cron job).
    """

    most_recent = models.ForeignKey(
        "Course",
        related_name="+",
        on_delete=models.PROTECT,
        help_text=dedent(
            """
        The most recent course (by semester) of this topic. You must change the corresponding
        `Topic` object's `most_recent` field before deleting a Course if it is the
        `most_recent` course (`on_delete=models.PROTECT`).
        """
        ),
    )

    historical_probabilities_spring = models.FloatField(
        default=0,
        help_text=dedent(
            """
        The historical probability of a student taking a course in this topic in the spring
        semester, based on historical data. This field is recomputed nightly from the
        `parent_course` graph (in the recompute_soft_state cron job).
        """
        ),
    )
    historical_probabilities_summer = models.FloatField(
        default=0,
        help_text=dedent(
            """
        The historical probability of a student taking a course in this topic in the summer
        semester, based on historical data. This field is recomputed nightly from the
        `parent_course` graph (in the recompute_soft_state cron job).
        """
        ),
    )
    historical_probabilities_fall = models.FloatField(
        default=0,
        help_text=dedent(
            """
        The historical probability of a student taking a course in this topic in the fall
        semester, based on historical data. This field is recomputed nightly from the
        `parent_course` graph (in the recompute_soft_state cron job).
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

    def __str__(self):
        return f"Topic {self.id} ({self.most_recent.full_code} most recently)"


class Attribute(models.Model):
    """
    A post-NGSS registration attribute, which is used to
    mark courses which students in a program/major should take.
    e.g. WUOM for the "Wharton OIDD Operation" track

    Note that Attributes (like Restrictions) do not have an associated
    semester.
    """

    code = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text=dedent(
            """
        A registration attribute code, for instance 'WUOM' for Wharton OIDD Operations track.
        """
        ),
    )

    description = models.TextField(
        help_text=dedent(
            """
        The registration attribute description, e.g. 'Wharton OIDD Operation'
        for the WUOM attribute.
        """
        )
    )

    SCHOOL_CHOICES = (
        ("SAS", "School of Arts and Sciences"),
        ("LPS", "College of Liberal and Professional Studies"),
        ("SEAS", "Engineering"),
        ("DSGN", "Design"),
        ("GSE", "Graduate School of Education"),
        ("LAW", "Law School"),
        ("MED", "School of Medicine"),
        ("MODE", "Grade Mode"),
        ("VET", "School of Veterinary Medicine"),
        ("NUR", "Nursing"),
        ("WH", "Wharton"),
    )

    school = models.CharField(
        max_length=5,
        choices=SCHOOL_CHOICES,
        db_index=True,
        null=True,
        help_text=dedent(
            """
        What school/program this attribute belongs to, e.g. `SAS` for `ASOC` restriction
        or `WH` for `WUOM` or `MODE` for `QP`. Options and meanings:
        """
            + string_dict_to_html(dict(SCHOOL_CHOICES))
        ),
    )

    courses = models.ManyToManyField(
        Course,
        related_name="attributes",
        blank=True,
        help_text=dedent(
            """
            Course objects which have this attribute
            """
        ),
    )

    def __str__(self):
        return f"{self.code} @ {self.school} - {self.description}"


class NGSSRestriction(models.Model):
    """
    A restriction on who can register for this course.

    Note that Restrictions (like Attributes) do not have an associated
    semester.
    """

    code = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        help_text=dedent(
            """
        The code of the restriction.
        """
        ),
    )

    restriction_type = models.CharField(
        max_length=25,
        db_index=True,
        help_text=dedent(
            """
        What the restriction is based on (e.g., Campus).
        """
        ),
    )

    inclusive = models.BooleanField(
        help_text=dedent(
            """
        Whether this is an include or exclude restriction. Corresponds to the `incl_excl_ind`
        response field. `True` if include (ie, `incl_excl_ind` is "I") and `False`
        if exclude ("E").
        """
        )
    )

    description = models.TextField(
        help_text=dedent(
            """
        The registration restriction description.
        """
        )
    )

    @staticmethod
    def special_approval():
        return NGSSRestriction.objects.filter(restriction_type="Special Approval")

    def __str__(self):
        return f"{self.code} - {self.restriction_type} - {self.description}"


class SectionManager(models.Manager):
    def get_queryset(self):
        return sections_with_reviews(super().get_queryset()).distinct()


class PreNGSSRestriction(models.Model):
    """
    A pre-NGSS (deprecated since 2022B) registration restriction,
    e.g. PDP (permission needed from department)
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

    @staticmethod
    def special_approval():
        return PreNGSSRestriction.objects.filter(code__in=PRE_NGSS_PERMIT_REQ_RESTRICTION_CODES)

    def __str__(self):
        return f"{self.code} - {self.description}"


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
        ("", "Undefined"),
        ("CLN", "Clinic"),
        ("CRT", "Clinical Rotation"),
        ("DAB", "Dissertation Abroad"),
        ("DIS", "Dissertation"),
        ("DPC", "Doctoral Program Exchange"),
        ("FLD", "Field Work"),
        ("HYB", "Hybrid"),
        ("IND", "Independent Study"),
        ("LAB", "Lab"),
        ("LEC", "Lecture"),
        ("MST", "Masters Thesis"),
        ("ONL", "Online"),
        ("PRC", "Practicum"),
        ("REC", "Recitation"),
        ("SEM", "Seminar"),
        ("SRT", "Senior Thesis"),
        ("STU", "Studio"),
    )

    class Meta:
        unique_together = (("code", "course"),)

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
    crn = models.CharField(
        max_length=8,
        db_index=True,
        blank=True,
        null=True,
        help_text=dedent(
            """
        The CRN ID of the section.
        Only available on sections after spring 2022 (i.e. after the NGSS transition).
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

    code_specific_enrollment = models.IntegerField(
        default=0,
        help_text=dedent(
            """
            The number students enrolled in this specific section as of our last registrarimport,
            NOT including crosslisted sections. Comparable with `.code_specific_capacity`.
            This field is not usable for courses before 2022B
            (first semester after the Path transition).
            """
        ),
    )
    code_specific_capacity = models.IntegerField(
        default=0,
        help_text=dedent(
            """
            The max allowed enrollment for this specific section,
            NOT including crosslisted sections.
            This field is not usable for courses before 2022B
            (first semester after the Path transition).
            """
        ),
    )

    enrollment = models.IntegerField(
        default=0,
        help_text=dedent(
            """
            The number students enrolled in all crosslistings of this section,
            as of our last registrarimport. Comparable with `.capacity`.
            SOFT STATE, recomputed by `recompute_soft_state` after each registrarimport as
            the sum of `.code_specific_enrollment` across all crosslisted sections.
            This field is not usable for courses before 2022B
            (first semester after the Path transition).
            """
        ),
    )
    capacity = models.IntegerField(
        default=0,
        help_text="The max allowed enrollment across all crosslistings of this section.",
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
            Maintained by the registrar import / recompute_soft_state script.
            """
        ),
    )

    instructors = models.ManyToManyField(
        Instructor,
        help_text="The Instructor object(s) of the instructor(s) teaching the section.",
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
    ngss_restrictions = models.ManyToManyField(
        NGSSRestriction,
        related_name="sections",
        blank=True,
        help_text=(
            "All NGSS registration Restriction objects to which this section is subject. "
            "This field will be empty for sections in 2022B or later."
        ),
    )
    pre_ngss_restrictions = models.ManyToManyField(
        PreNGSSRestriction,
        related_name="sections",
        blank=True,
        help_text=(
            "All pre-NGSS (deprecated since 2022B) registration Restriction objects to which "
            "this section is subject. This field will be empty for sections "
            "in 2022B or later."
        ),
    )

    credits = models.DecimalField(
        max_digits=4,  # some course for 2019C is 14 CR...
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
        help_text="The number of credits this section is worth.",
    )

    has_reviews = models.BooleanField(
        default=False,
        help_text=dedent(
            """
            A flag indicating whether this section has reviews (precomputed for efficiency).
            """
        ),
    )
    has_status_updates = models.BooleanField(
        default=False,
        help_text=dedent(
            """
            A flag indicating whether this section has Status Updates (precomputed for efficiency).
            """
        ),
    )

    registration_volume = models.PositiveIntegerField(
        default=0,
        help_text="The number of active PCA registrations watching this section.",
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
                    section=self,
                    created_at__gt=add_drop_start,
                    created_at__lt=add_drop_end,
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

    STATUS_CHOICES = (
        ("O", "Open"),
        ("C", "Closed"),
        ("X", "Cancelled"),
        ("", "Unlisted"),
    )
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
        default=False,
        help_text="Was this status update created during the add/drop period?",
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
        from alert.tasks import section_demand_change
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

        self.section.has_status_updates = True
        self.section.save()

        section_demand_change.delay(self.section.id, self.created_at)


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
        max_length=8,
        help_text="The room number, e.g. `101` for Wu and Chen Auditorium in Levine.",
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
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        help_text=dedent(
            """
        The Room object in which the meeting is taking place
        (null if this is an online meeting).
        """
        ),
    )

    start_date = models.TextField(
        blank=True,
        null=True,
        max_length=10,
        help_text=dedent(
            """
        The first day this meeting takes place, in the form 'YYYY-MM-DD', e.g. '2022-08-30'.
        Not available for sections offered in or before spring 2022.
        """
        ),
    )
    end_date = models.TextField(
        blank=True,
        null=True,
        max_length=10,
        help_text=dedent(
            """
        The last day this meeting takes place, in the form 'YYYY-MM-DD', e.g. '2022-12-12'.
        Not available for sections offered in or before spring 2022.
        """
        ),
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
PreNGSSRequirement
"""


class PreNGSSRequirement(models.Model):
    """
    A pre-NGSS (deprecated since 2022B) academic requirement which the specified course(s)
    fulfill(s). Not to be confused with PreNGSSRestriction objects, which were restrictions
    on registration for certain course section(s).
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
        related_name="pre_ngss_requirements",
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
        related_name="pre_ngss_requirement_set",
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
        related_name="pre_ngss_nonrequirement_set",
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
        [phonenumbers library](https://pypi.org/project/phonenumbers/) and also valid.

        Note: validators are NOT called automatically on model object save. They are called
        on `object.full_clean()`, and also on serializer validation (returning a 400 if violated).
        https://docs.djangoproject.com/en/4.2/ref/validators/
        """
        if not value or not value.strip():
            return
        try:
            parsed_number = phonenumbers.parse(value, "US")
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValueError(f"Invalid phone number '{value}'.")
        except (phonenumbers.phonenumberutil.NumberParseException, ValueError) as e:
            raise ValidationError(str(e))

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
        if not self.phone or not self.phone.strip():
            self.phone = None
        if self.phone:
            # self.phone should be validated by `validate_phone`
            phone_number = phonenumbers.parse(self.phone, "US")
            self.phone = phonenumbers.format_number(
                phone_number, phonenumbers.PhoneNumberFormat.E164
            )
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


class Friendship(models.Model):
    """
    Used to track friendships along with requests status
    """

    sender = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        null=True,
        related_name="sent_friendships",
        help_text="The person (user) who sent the request.",
    )

    recipient = models.ForeignKey(
        get_user_model(),
        related_name="received_friendships",
        on_delete=models.CASCADE,
        null=True,
        help_text="The person (user) who recieved the request.",
    )

    class Status(models.TextChoices):
        SENT = "S", "Sent"
        ACCEPTED = "A", "Accepted"
        REJECTED = "R", "Rejected"

    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.SENT,
    )

    def are_friends(self, user1_id, user2_id):
        """
        Checks if two users are friends (lookup by user id)
        """
        return Friendship.objects.filter(
            Q(sender_id=user1_id, recipient_id=user2_id, status=Friendship.Status.ACCEPTED)
            | Q(sender_id=user2_id, recipient_id=user1_id, status=Friendship.Status.ACCEPTED)
        ).exists()

    def save(self, *args, **kwargs):
        if self.status == self.Status.ACCEPTED and self.accepted_at is None:
            self.accepted_at = timezone.now()
        if self.status == self.Status.REJECTED:
            self.accepted_at = None
            self.sent_at = None
        if self.status == self.Status.SENT and self.sent_at is None:
            self.sent_at = timezone.now()
        super().save(*args, **kwargs)

    accepted_at = models.DateTimeField(null=True)
    sent_at = models.DateTimeField(null=True)

    class Meta:
        unique_together = (("sender", "recipient"),)

    def __str__(self):
        return (
            f"Friendship(Sender: {self.sender}, Recipient: {self.recipient}, Status: {self.status})"
        )

class Comment(models.Model):
    """
    A single comment associated with a topic to be displayed on PCR. Comments support replies
    through the parent_id and path fields. The path field allows for efficient database querying
    and can indicate levels of nesting and can make pagination simpler. Idea implemented based
    on this guide: https://blog.miguelgrinberg.com/post/implementing-user-comments-with-sqlalchemy.
    """

    # Log base 10 value of maximum adjacent comment length.
    _N = 10

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        get_user_model(),
        on_delete = models.SET_NULL,
        null=True,
        related_name="comments"
    )
    upvotes = models.ManyToManyField(
        get_user_model(),
        related_name="upvotes",
        help_text="The number of upvotes a comment gets."
    )
    downvotes = models.ManyToManyField(
        get_user_model(),
        related_name="downvotes",
        help_text="The number of downvotes a comment gets."
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        default=None,
        help_text=dedent(
            """
        The section with which a comment is associated. Section was chosen instead of courses
        for hosting topics to support lower levels of filtering.
        """
        )
    )

    parent_id = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL, # redundant due to special deletion conditions
        null=True
    )
    path = models.TextField(db_index=True)

    def level(self):
        return len(self.path.split('.'))
    def save(self, **kwargs):
        prefix = self.parent.path + '.' if self.parent else ''
        self.path = prefix + '{:0{}d}'.format(self.id, self._N)
        super().save(**kwargs)
    def delete(self, **kwargs):
        if Comment.objects.filter(parent_id=self).exists():
            self.text = "This comment has been removed."
            self.likes.clear()
            self.author = None
            self.save()
        else:
            super().delete(**kwargs)
    def __str__(self):
        return f"{self.author}: {self.text}"