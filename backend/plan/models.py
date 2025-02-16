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
        blank=True,
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

    @property
    def is_primary(self):
        return hasattr(self, "primary_schedule")

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



class Break(models.Model):
    """
    Holds break objects created by users on PCP.
    """

    person = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        help_text="The person (user) who created this break.",
    )

    location_string = models.CharField(
        max_length=80,
        null=True,
        help_text=dedent(
            """
            This represents the location that the user can input themselves. 
            Will use a building object from a drop down or have it validated or something so it can interact with map.
            Didn't want to run into issue of users creating arbitrary Room objects, so just using a char field
            """
        ) #TODO: Don't know how I want to do buildings yet.
    )

    name = models.CharField(
        max_length=255,
        help_text=dedent(
            """
        The user's name for the break. No two breaks can match in all of the fields
        `[name, person]`
        """
        ),
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
    
    class Meta:
        unique_together = (("person"),)

    def __str__(self):
        return "User: %s, Break ID: %s" % (self.person, self.id)


