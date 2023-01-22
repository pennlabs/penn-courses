from textwrap import dedent

from django.contrib.auth import get_user_model
from django.db import models

from courses.models import Section


class Schedule(models.Model):
    """
    Used to save schedules created by users on PCP
    """

    person = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        help_text="The person (user) to which the schedule belongs.",
    )

    sections = models.ManyToManyField(
        Section,
        help_text=dedent(
            """
        The class sections which comprise the schedule. The semester of each of these sections is
        assumed to  match the semester defined by the semester field below.
        """
        ),
    )

    semester = models.CharField(
        max_length=5,
        help_text=dedent(
            """
        The academic semester planned out by the schedule (of the form YYYYx where x is A
        [for spring], B [summer], or C [fall]), e.g. `2019C` for fall 2019.
        """
        ),
    )

    name = models.CharField(
        max_length=255,
        help_text=dedent(
            """
        The user's nick-name for the schedule. No two schedules can match in all of the fields
        `[name, semester, person]`
        """
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("name", "semester", "person"),)

    def __str__(self):
        return "User: %s, Schedule ID: %s" % (self.person, self.id)


class PrimarySchedule(models.Model):
    """
    Used to save the primary schedule for a user. This is the schedule that is displayed
    on the main page.
    """

    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
        null=True,
        related_name="primary_schedule",
        help_text="The User to which this schedule belongs.",
    )

    schedule = models.OneToOneField(
        Schedule,
        on_delete=models.CASCADE,
        null=True,
        related_name="primary_schedule",
        help_text="The schedule that is the primary schedule for the user.",
    )

    class Meta:
        # for now, we only allow one primary schedule per user
        unique_together = (("user",),)

    def __str__(self):
        return f"PrimarySchedule(User: {self.user}, Schedule ID: {self.schedule_id})"