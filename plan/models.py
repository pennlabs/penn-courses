from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from courses.models import Section


class Schedule(models.Model):
    """
    Used to save schedules created by users on PCP
    """
    person = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    sections = models.ManyToManyField(Section)

    semester = models.CharField(max_length=5)

    name = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('name', 'semester', 'person'), )

    def save(self, *args, **kwargs):
        super(Schedule, self).save(*args, **kwargs)
        for s in self.sections.all():
            if self.semester != s.course.semester:
                raise ValidationError('Sections do not match semester')

    def __str__(self):
        return 'User: %s, Schedule ID: %s' % (self.person, self.id)
