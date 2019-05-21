from django.db import models


class ReviewAverage(models.Model):
    section_id = models.CharField(max_length=16)
    instructor = models.ForeignKey('courses.Instructor', on_delete=models.CASCADE)

    # review fields
    course_quality = models.DecimalField(max_digits=3, decimal_places=2)
    difficulty = models.DecimalField(max_digits=3, decimal_places=2)
    instructor_quality = models.DecimalField(max_digits=3, decimal_places=2)
    work_required = models.DecimalField(max_digits=3, decimal_places=2)

    class Meta:
        unique_together = (('section_id', 'instructor'), )
