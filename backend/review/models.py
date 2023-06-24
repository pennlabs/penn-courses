from django.db import models
from django.db.models import Avg, Q, UniqueConstraint


class Review(models.Model):
    """
    Represents the aggregate review for an instructor for a single section of a course.
    By virtue of being associated to a course, every semester of a course will have a new Review
    object.

    Actual scores for the review is stored in the ReviewBit related object, can be accessed via the
    `reviewbit_set` of the object.
    """

    # sections have at most one review per instructor attached to the section.
    section = models.ForeignKey("courses.Section", on_delete=models.CASCADE)
    instructor = models.ForeignKey("courses.Instructor", on_delete=models.CASCADE)

    enrollment = models.IntegerField(blank=True, null=True)
    responses = models.IntegerField(blank=True, null=True)
    form_type = models.IntegerField(blank=True, null=True)

    comments = models.TextField(blank=True)

    class Meta:
        unique_together = (("section", "instructor"),)

    def __str__(self):
        return f"{self.section} - {self.instructor}"

    def set_averages(self, bits):
        for key, value in bits.items():
            ReviewBit.objects.update_or_create(review=self, field=key, defaults={"average": value})

    @staticmethod
    def get_averages(topic_id, instructor_name=None, fields=None):
        if fields is None:
            # Default fields (topline numbers on PCR)
            fields = [
                "course_quality",
                "difficulty",
                "instructor_quality",
            ]

        # We're using some of the aggregation tricks documented on Django's Aggregation Cheat Sheet:
        # https://docs.djangoproject.com/en/2.2/topics/db/aggregation/#cheat-sheet

        # Filter down a queryset to just include this course
        qs = Review.objects.filter(section__course__topic_id=topic_id, responses__gt=0)
        if (
            instructor_name is not None
        ):  # if an instructor is specified, filter down to just that instructor
            qs = qs.filter(instructor_name__contains=instructor_name)

        # pass each aggregation as its own argument to `aggregate` (using dictionary comprehensions)
        return qs.aggregate(
            **{
                # average the average of all the reviewbits of a certain field
                # (that's where the filter comes in)
                field: Avg("reviewbit__average", filter=Q(reviewbit__field=field))
                for field in fields
            }
        )


"""
Review Bits have different labels in the summary table and the rating table.
This tuple keeps track of the association between the two, along with an
intermediate, general label that we use internally.
"""
REVIEW_BIT_LABEL = (
    ("RINSTRUCTORQUALITY", "Instructor Quality", "instructor_quality"),
    ("RCOURSEQUALITY", "Course Quality", "course_quality"),
    ("RCOMMABILITY", "Comm. Ability", "communication_ability"),
    ("RSTIMULATEINTEREST", "Stimulate Ability", "stimulate_interest"),
    ("RINSTRUCTORACCESS", "Instructor Access", "instructor_access"),
    ("RDIFFICULTY", "Difficulty", "difficulty"),
    ("RWORKREQUIRED", "Work Required", "work_required"),
    ("RTAQUALITY", "TA Quality", "ta_quality"),
    ("RREADINGSVALUE", "Readings Value", "readings_value"),
    ("RAMOUNTLEARNED", "Amount Learned", "amount_learned"),
    ("RRECOMMENDMAJOR", "Recommend Major", "recommend_major"),
    ("RRECOMMENDNONMAJOR", "Recommend Non-Major", "recommend_nonmajor"),
    ("RABILITIESCHALLENGED", "Abilities Challenged", "abilities_challenged"),
    ("RCLASSPACE", "Class Pace", "class_pace"),
    ("RINSTRUCTOREFFECTIVE", "Instructor Effectiveness", "instructor_effective"),
    ("RNATIVEABILITY", "Native Ability", "native_ability"),
)

# Maps column name from SUMMARY sql tables to common slug.
COLUMN_TO_SLUG = {x[0]: x[2] for x in REVIEW_BIT_LABEL}
# Maps "context" value from RATING table to common slug.
CONTEXT_TO_SLUG = {x[1]: x[2] for x in REVIEW_BIT_LABEL}
ALL_FIELD_SLUGS = [x[2] for x in REVIEW_BIT_LABEL]


class ReviewBit(models.Model):
    """
    A single key/value pair associated with a review. Fields are things like "course_quality",
    and averages which range from 0 to 4.
    """

    review = models.ForeignKey(Review, on_delete=models.CASCADE)
    field = models.CharField(max_length=32, db_index=True)

    average = models.DecimalField(max_digits=6, decimal_places=5)
    median = models.DecimalField(max_digits=6, decimal_places=5, null=True, blank=True)
    stddev = models.DecimalField(max_digits=6, decimal_places=5, null=True, blank=True)

    # The integer counts for how many students rated 0-4 on a given property.
    rating0 = models.IntegerField(null=True, blank=True)
    rating1 = models.IntegerField(null=True, blank=True)
    rating2 = models.IntegerField(null=True, blank=True)
    rating3 = models.IntegerField(null=True, blank=True)
    rating4 = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = (("review", "field"),)

    def __str__(self):
        return f"#{self.review.pk} - {self.field}: {self.average}"


class BaseAverageBit(models.Model):
    """
    Like review.models.ReviewBit, but with only an average field.
    """
    field = models.CharField(max_length=32, db_index=True)
    average = models.DecimalField(max_digits=6, decimal_places=5)

class BaseReviewAverage(models.Model):
    """
    The reviews for a model (e.g., topic or instructor). 
    This is used to cache the reviews for a given instance of that model. 
    It is expected that subclasses of BaseReviewAverage will be instantiated by a cron job.

    The average_or_recent field is used to distinguish between the average and recent reviews.
    """
    updated_at = models.DateTimeField(auto_now=True)
    average_or_recent = models.BooleanField()

# Cache Topic Reviews
class TopicReviews(BaseReviewAverage):
    topic = models.ForeignKey("courses.Topic", on_delete=models.CASCADE)
    class Meta:
        UniqueConstraint(fields=['instructor', 'average_or_recent'], name='unique_instructor_average_or_recent')

class TopicReviewBit(BaseAverageBit):
    topic_reviews = models.ForeignKey(TopicReviews, on_delete=models.CASCADE, related_name='bits', db_index=True)
    class Meta:
        UniqueConstraint(fields=['topic_reviews', 'field'], name='unique_topic_reviews_field')

# Cache Instructor Reviews
class InstructorReviews(BaseReviewAverage):    
    instructor = models.ForeignKey("courses.Instructor", on_delete=models.CASCADE)
    class Meta:
        UniqueConstraint(fields=['instructor', 'average_or_recent'], name='unique_instructor_average_or_recent')

class InstructorReviewBit(BaseAverageBit):
    instructor_reviews = models.ForeignKey(InstructorReviews, on_delete=models.CASCADE, related_name='bits', db_index=True)
    class Meta:
        UniqueConstraint(fields=['instructor_reviews', 'field'], name='unique_instructor_reviews_field')

# Cache Department Reviews
class DepartmentReviews(BaseReviewAverage):    
    instructor = models.ForeignKey("courses.Department", on_delete=models.CASCADE)
    class Meta:
        UniqueConstraint(fields=['department', 'average_or_recent'], name='unique_department_average_or_recent')

class DepartmentReviewBit(BaseAverageBit):
    department_average = models.ForeignKey(DepartmentReviews, on_delete=models.CASCADE, related_name='bits', db_index=True)
    class Meta:
        UniqueConstraint(fields=['department_reviews', 'field'], name='unique_instructor_reviews_field')