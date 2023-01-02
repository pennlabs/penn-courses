from django.db import models
from textwrap import dedent
from django.contrib.auth import get_user_model

from courses.models import Topic, Course, string_dict_to_html


class Degree(models.Model):
    """
    This model represents a degree.
    """

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text=dedent(
            """
        The name of this degree
        """
        ),
    )
    credits = models.IntegerField(
        help_text=dedent(
            """
        The number of credits required for this degree.    
        """
        )
    )

    def __str__(self):
        return "Name: %s, Degree ID: %s" % (self.name, self.id)


class DegreeRequirement(models.Model):
    """
    This model represents a degree requirement as a recursive tree.
    """
    SATISFIED_BY = (
        ("ALL", "Not an actual satisfied by mode: represented by NUM_COURSES where num = number of courses. Must "
                "take all courses to satisfy requirements"),
        ("ANY", "Not an actual satisfied by mode: represented by NUM_COURSES where num = 1. Can take any course to "
                "satisfy requirements."),
        ("CUS", "Must take courses with total number of CUs to satisfy requirements"),
        ("NUM_COURSES", "Must take a certain number of courses to satisfy requirements"),
    )

    class SatisfiedBy(models.IntegerChoices):
        ALL = 1
        CUS = 2
        NUM_COURSES = 3

    name = models.TextField(
        help_text=dedent(
            """
        The name of the requirement.
        """
        )
    )
    satisfied_by = models.IntegerField(
        choices=SatisfiedBy.choices,
        db_index=False,  # TODO: is db_index true or false here?
        null=True,
        help_text=dedent(
            """
        The way in which this requirement is satisfied.  This is a string, and can be one of the
        following:
        """
            + string_dict_to_html(dict(SATISFIED_BY))
        ),
    )
    q = models.TextField(
        max_length=1000,
        null=True,
        help_text=dedent(
            """
        Used to store more complex & larger query sets using the same interface as Q() objects. Not null if and only iff
        courses is blank/empty.
        """
        )
    )
    topics = models.ManyToManyField(
        Topic,
        related_name="requirements",
        blank=True,
        help_text=dedent(
            """
            Course objects which have this requirement.
            """
        ),
    )
    num = models.IntegerField(
        null=True,
        help_text=dedent(
            """
        The number of CUs or Courses required to satisfy this requirement
        """
        ),
    )
    degree = models.ForeignKey(
        Degree,
        on_delete=models.CASCADE,
        null=True,
        default=None,
        related_name="requirements",
        help_text=dedent(
            """
        The degree this requirement falls under.
        """
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True) # TODO: do we need these fields?
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} @ {self.topics} - {self.cus}"

    def fulfills(self, course):
        return self.topics.all().contains(course.topic)

    class Meta:
        unique_together = (("name", "degree"),)


class DegreeFulfillment(models.Model):
    """
    This model represents a course fulfilling requirements.

    Note: this model is not tied to a user, but the DegreePlan model is.
    """
    STATUS = (
        ("TAKEN", "course has already been taken"),
        ("IN_PROGRESS", "course is currently in progress (in the current semester)"),
        ("PLANNED", "course is planned for the future"),
    )

    class Status(models.IntegerChoices): # TODO: can we just infer this from the semester
        TAKEN = 1
        IN_PROGRESS = 2 # TODO: is this necessary
        PLANNED = 3

    degree_plan = models.ForeignKey(
        "DegreePlan",
        on_delete=models.CASCADE,
        null=True,
        default=None,
        related_name="fulfillments",
        help_text=dedent(
            """
        The degree plan this semester plan is a part of.
        """
        ),
    )
    status = models.IntegerField(
        choices=Status.choices,
        null=True,
        help_text=dedent(
            """
        The way in which this requirement is satisfied.  This is a string, and can be one of the
        following:
        """
            + string_dict_to_html(dict(STATUS))
        ),
    )
    semester = models.CharField(
        max_length=5,
        db_index=True,
        help_text=dedent(
            """
        The academic semester this degree fulfillment is applicable to, like `2021C`.
        """
        ),
    )
    course = models.ForeignKey( # TODO: should be topic?
        Course,
        on_delete=models.CASCADE, # TODO: is cascade the right behavior here
        help_text=dedent(
            """
        The fulfilling course.
        """
        ),
    )
    fulfilled_requirements = models.ManyToManyField(
        "DegreeRequirement",
        help_text=dedent(
            """
        The requirement(s) this fulfils.
        """
        ),
    ) # TODO: set related name?
    overridden = models.BooleanField(
        help_text=dedent(
            """
        Whether this is an override for one or more requirements.
        """
        ), # TODO: this is actually a terrible way of representing this: what if we only want to override to fulfil 1 req?
    )

    class Meta:
        unique_together = (("degree_plan", "semester", "course"),)

class DegreePlan(models.Model):
    """
    Used to create degree plans.
    """

    person = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        help_text="The person (user) to which the degree plan belongs.",
    )
    name = models.CharField(
        max_length=255,
        help_text=dedent(
            """
        The user's nick-name for the degree plan. No two plans can match in all of the fields
        `[name, person]`
        """
        ),
    )
    degree = models.ForeignKey(
        Degree,
        on_delete=models.RESTRICT,
    )
    cart = models.ManyToManyField(
        Course,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(
        help_text=dedent(
            """
        Used to store any notes about the degree (for instance, the superscript notes on Penn's Catalog)
        """
        ),
    )

    class Meta:
        unique_together = (("name", "person"),)

    def __str__(self):
        return "User: %s, DegreePlan ID: %s" % (self.person, self.id)