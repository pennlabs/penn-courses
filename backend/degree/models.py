from django.db import models
from textwrap import dedent
from django.contrib.auth import get_user_model

from courses.models import Topic, Course


class Degree(models.Model):
    """
    This model represents a degree.
    """

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text=dedent(
            """
        The name of this requirement. No two schedules can match in all of the fields
        `[name, semester, person]`
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
    semester = models.CharField(
        max_length=5,
        help_text=dedent(
            """
        The academic semester this degree requirement is applicable to.
        """
        ), # TODO: remove?
    )
    name = models.CharField(
        max_length=255,
        help_text=dedent(
            """
        The name of this requirement.
        """
        ),
    )
    num_courses = models.IntegerField(
        null=True,
        help_text=dedent(
            """
        The number of courses required to fulfil this requirement. Can be null if this
        requirement does not have a number of courses associated. Note that only one of
        num_courses and num_credits should be null.
        """
        ),
    )
    num_credits = models.IntegerField(
        null=True,
        help_text=dedent(
            """
        The number of courses units (CUs) required to fulfil this requirement. Can be null if this
        requirement does not have a number of CUs. Note that only one of num_courses and num_credits should
        be null.
        """
        ),
    )
    inclusive = models.BooleanField(
        help_text=dedent(
            """
        Whether the `topics` fields are the courses that fulfill this requirement (inclusive -> True),
        or are the set of courses that do not fulfill the requirement (exclusive -> False).
        """
        )
    )
    topics = models.ManyToManyField(
        Topic,
        related_name="degree_requirements"
    )

    class Meta:
        unique_together = (("name", "semester", "degree"),) # TODO: should be just name & semester?

    def __str__(self):
        return "Name: %s, DegreeRequirement ID: %s" % (self.name, self.id)


class DegreeFulfillment(models.Model):
    """
    This model represents a course fulfilling requirements.

    Note: this model is not tied to a user, but the DegreePlan model is.
    """

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
    semester = models.CharField(
        max_length=5,
        db_index=True,
        help_text=dedent(
            """
        The academic semester this degree fulfillment is applicable to.
        """
        ),
    )
    course = models.ManyToManyField( # TODO: should be topic?
        Course,
        null=True,
        related_name="semester_plans",
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
    created_at = models.DateTimeField(auto_now_add=True) # TODO: do we need these fields?
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("name", "person"),)

    def __str__(self):
        return "User: %s, DegreePlan ID: %s" % (self.person, self.id)