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
    is_adv_reg = models.BooleanField(
        default=False,
        db_index=True,
        help_text=dedent(
            """
            Whether this schedule is from advanced registration. Schedules of this type are hidden
            on the front end.
        """
        ),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("name", "semester", "person"),)

    def __str__(self):
        return "User: %s, Schedule ID: %s" % (self.person, self.id)
