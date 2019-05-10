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


class Department(models.Model):
    code = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.code


class Course(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    code = models.CharField(max_length=8)
    semester = models.CharField(max_length=5)

    title = models.TextField()
    description = models.TextField(blank=True)

    # Handle crosslisted courses.
    # All crosslisted courses have a "primary listing" in the registrar.
    primary_listing = models.ForeignKey('Course',
                                        related_name='listing_set',
                                        on_delete=models.CASCADE,
                                        null=True,
                                        blank=True)

    class Meta:
        unique_together = (('department', 'code', 'semester'), )

    def __str__(self):
        return '%s %s' % (self.course_id, self.semester)

    @property
    def course_id(self):
        return '%s-%s' % (self.department, self.code)

    @property
    def crosslistings(self):
        if self.primary_listing is not None:
            return self.primary_listing.listing_set
        else:
            return None


class Restriction(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField()

    @property
    def permit_required(self):
        return 'permission' in self.description.lower()


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
    restrictions = models.ManyToManyField(Restriction)

    credits = models.DecimalField(max_digits=3,
                                  decimal_places=2,
                                  null=True,
                                  blank=True)

    prereq_notes = models.TextField(blank=True)

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


"""
Requirements
"""


class Requirement(models.Model):
    SCHOOL_CHOICES = (
        ('SEAS', 'Engineering'),
        ('WH17-', 'Wharton 2017-'),
        ('WH17+', 'Wharton 2017+'),
        ('SAS', 'College')
    )
    # organize requirements by semester so that we don't get huge related sets which don't give particularly good
    # info.
    semester = models.CharField(max_length=5)
    # code identifying this requirement
    code = models.CharField(max_length=10)
    # what school this requirement belongs to
    school = models.CharField(max_length=5, choices=SCHOOL_CHOICES)
    # whether or not this entry is saying that these courses fulfill a requirement or not
    satisfies = models.BooleanField()
    # name of the requirement
    name = models.CharField(max_length=255)

    # Departments which satisfy (or don't) this requirement
    departments = models.ManyToManyField(Department, related_name='requirements')
    # Course-level overrides for when a specific course's requirements are different
    # from its departments'
    courses = models.ManyToManyField(Course, related_name='overrides')

    '''
    As a general rule, if satisfies==False, there should NOT be departments in the requirement.
    satisfies operates as a way to *override* for specific courses within a department.
    Generally, if a department is not related to a requirement, then it DOES NOT satisfy that
    requirement. Same for a specific course.
    '''

    class Meta:
        unique_together = (('semester', 'code', 'satisfies'), )
