from django.db import models

from options.models import get_value


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

    name = models.TextField()

    def __str__(self):
        return self.name


class Course(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    department = models.CharField(max_length=8)
    code = models.CharField(max_length=8)
    semester = models.CharField(max_length=5)

    title = models.TextField()
    description = models.TextField(blank=True)

    # Handle crosslisted courses.
    # All crosslisted courses have a "primary listing" in the registrar.
    primary_listing = models.ForeignKey('Course', related_name='listing_set', on_delete=models.CASCADE)

    class Meta:
        unique_together = (('department', 'code', 'semester'), )

    def __str__(self):
        return '%s %s' % (self.course_id, self.semester)

    @property
    def course_id(self):
        return '%s-%s' % (self.department, self.code)

    @property
    def crosslistings(self):
        return self.primary_listing.listing_set


class Section(models.Model):
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
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    status = models.CharField(max_length=4, choices=STATUS_CHOICES)

    capacity = models.IntegerField(default=0)
    activity = models.CharField(max_length=50, choices=ACTIVITY_CHOICES)
    meeting_times = models.TextField(blank=True)
    instructors = models.ManyToManyField(Instructor)

    associated_sections = models.ManyToManyField('Section')

    credits = models.DecimalField(max_digits=3, decimal_places=2)

    def __str__(self):
        return '%s-%s %s' % (self.course.course_id, self.code, self.course.semester)

    @property
    def normalized(self):
        """String used for querying updates to this section with the Penn API"""
        return '%s-%s' % (self.course.course_id, self.code)

    @property
    def is_open(self):
        return self.status == 'O'


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
    created_at = models.DateTimeField(auto_now_add=True)
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


class Room(models.Model):
    """ A room in a Building. It optionally may be named. """
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    number = models.CharField(max_length=5)
    name = models.CharField(max_length=80)

    class Meta:
        """ To hold uniqueness constraint """
        unique_together = (("building", "number"),)


class Meeting(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='meetings')
    day = models.CharField(max_length=1)
    # the time hh:mm is formatted as decimal hhmm, i.e. h*100 + m
    start = models.IntegerField()
    end = models.IntegerField()
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
