import math
import uuid
from textwrap import dedent

import phonenumbers
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, Max, Min, OuterRef, Q, Subquery
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
        help_text="The department code, e.g. 'CIS' for the CIS department.",
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
        max_length=8, db_index=True, help_text="The course code, e.g. '120' for CIS-120."
    )
    semester = models.CharField(
        max_length=5,
        db_index=True,
        help_text=dedent(
            """
        The semester of the course (of the form YYYYx where x is A [for spring],
        B [summer], or C [fall]), e.g. 2019C for fall 2019.
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
        help_text="The dash-joined department and code of the course, e.g. 'CIS-120' for CIS-120.",
    )

    prerequisites = models.TextField(
        blank=True,
        help_text="Text describing the prereqs for a course, e.g. 'CIS 120, 160' for CIS-121.",
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

    class Meta:
        unique_together = (("department", "code", "semester"), ("full_code", "semester"))

    def __str__(self):
        return "%s %s" % (self.full_code, self.semester)

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


class Restriction(models.Model):
    """
    A registration restriction, e.g. PDP (permission needed from department),
    which CIS-120 happens to be subject to.
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


def normalize(value, min, max):
    """
    This function normalizes the given value to a 0-1 scale based on the given min and max.
    WARNING: ensure that max-min != 0 before calling this function.
    """
    return float(value - min) / float(max - min)


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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    code = models.CharField(
        max_length=16,
        db_index=True,
        help_text="The section code, e.g. '001' for the section CIS-120-001.",
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
        e.g. 'CIS-120-001' for the 001 section of CIS-120.
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
        "e.g. 220 for CIS-120-001 (2020A).",
    )
    activity = models.CharField(
        max_length=50,
        choices=ACTIVITY_CHOICES,
        db_index=True,
        help_text="The section activity, e.g. 'LEC' for CIS-120-001 (2020A). Options and meanings: "
        + string_dict_to_html(dict(ACTIVITY_CHOICES)),
    )
    meeting_times = models.TextField(
        blank=True,
        help_text=dedent(
            """
        A JSON-stringified list of meeting times of the form
        '{days code} {start time} - {end time}', e.g.
        '["MWF 09:00 AM - 10:00 AM","F 11:00 AM - 12:00 PM","T 05:00 PM - 06:00 PM"]' for
        PHYS-151-001 (2020A). Each letter of the days code is of the form M, T, W, R, F for each
        day of the work week, respectively (and multiple days are combined with concatenation).
        To access the Meeting objects for this section, the related field `meetings` can be used.
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

    def __str__(self):
        return "%s %s" % (self.full_code, self.course.semester)

    @property
    def current_popularity(self):
        """
        The current popularity of the section, which is defined as:
        [the number of active PCA registrations for this section]/[the class capacity]
        mapped onto the range [0,1] where the lowest current popularity (across all sections)
        maps to 0 and the highest current popularity maps to 1.
        NOTE: sections with an invalid class capacity (0 or negative) are excluded from
        computation of the statistic, and if this section has an invalid class capacity, then
        this property will equal None (or null in JSON).
        """
        from alert.models import Registration  # imported here to avoid circular imports
        if self.capacity == 0:
            return None
        aggregate_scores = (
            Registration.objects.filter(setion__capacity__gt=0)
            .values("section", "section__capacity")
            .annotate(score=Count("section") / Max("section__capacity"))
            .aggregate(min=Min("score"), max=Max("score"))
        )
        if aggregate_scores.min == aggregate_scores.max:
            return 0.5
        this_score = float(Registration.objects.filter(section=self).count()) / float(self.capacity)
        # normalize(...) maps the range [aggregate_scores.min, aggregate_scores.max] to [0,1] and
        # returns the position of this_score on this new range
        return normalize(this_score, aggregate_scores.min, aggregate_scores.max)

    @property
    def semester(self):
        """
        The semester of the course (of the form YYYYx where x is A [for spring],
        B [summer], or C [fall]), e.g. 2019C for fall 2019.
        """
        return self.course.semester

    @property
    def is_open(self):
        """
        True if self.status == "O", False otherwise
        """
        return self.status == "O"

    def save(self, *args, **kwargs):
        self.full_code = f"{self.course.full_code}-{self.code}"
        super().save(*args, **kwargs)


class StatusUpdate(models.Model):
    """
    A registration status update for a specific section (e.g. CIS-120 went from open to close)
    """

    STATUS_CHOICES = (("O", "Open"), ("C", "Closed"), ("X", "Cancelled"), ("", "Unlisted"))
    section = models.ForeignKey(
        Section,
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
    # equivalently, iff SEND_FROM_WEBHOOK == True and SEMESTER == course_term, and the request
    # is not otherwise invalid
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
        [-90.0, 90.0]), e.g. 39.961380 for the Towne Building.
        """
        ),
    )
    longitude = models.FloatField(
        blank=True,
        null=True,
        help_text=dedent(
            """
        The longitude of the building, in the signed decimal degrees format (global range of
        [-180.0, 180.0]), e.g. -75.176773 for the Towne Building.
        """
        ),
    )

    def __str__(self):
        return self.name if len(self.name) > 0 else self.code


class Room(models.Model):
    """ A room in a Building. It optionally may be named. """

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
        max_length=5, help_text="The room number, e.g. 101 for Wu and Chen Auditorium in Levine."
    )
    name = models.CharField(
        max_length=80,
        help_text="The room name (optional, empty string if none), e.g. 'Wu and Chen Auditorium'.",
    )

    class Meta:
        """ To hold uniqueness constraint """

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
        minute = (time % 1) * 60

        return f'{hour if hour != 0 else 12}:{minute if minute != 0 else "00"} {"AM" if time < 12 else "PM"}'  # noqa: E501

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

    def __str__(self):
        return f"{self.section}: {self.start_time}-{self.end_time} in {self.room}"


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
        or C [fall]), e.g. 2019C for fall 2019. We organize requirements by semester so that we
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
        What school this requirement belongs to, e.g. 'SAS' for the SAS 'Formal Reasoning Course'
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
        The code identifying this requirement, e.g. 'MFR' for 'Formal Reasoning Course',
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
        super(UserProfile, self).save(*args, **kwargs)


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
