from django.db import models
from django.db.models import Avg, Q
from django.contrib.auth import get_user_model
from courses.models import Course
from textwrap import dedent

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

class Comment(models.Model):
    """
    A single comment associated with a topic to be displayed on PCR. Comments support replies
    through the parent_id and path fields. The path field allows for efficient database querying
    and can indicate levels of nesting and can make pagination simpler. Idea implemented based
    on this guide: https://blog.miguelgrinberg.com/post/implementing-user-comments-with-sqlalchemy.
    """

    # Should I use viewset or bare API view? – default to viewset if possible, otherwise do bareAPIView
    # Course: get all comments for a course given its specific topics (GET)
    # CommentViewSet: get, put, post, delete

    # Getting comments (course_id)
    # This should implement the same logic as the review viewset code, where you take in a course
    # and get the comments that relate to all courses in the topic.

    # Adding a comment (comment_id)
    # Adding a comment should be allowed on any thread by any user.
    # If a comment is made with no parent_id, it should be a top-level comment.
    # If a comment is made with a parent_id, it will be added with a higher indentation level.

    # Editing a comment (comment_id)
    # Option to edit should only show up if the user posted the comment.
    # On the frontend, a comment should show "(edited)" if the comment's created_at and modified_at times are more than a second apart.

    # Deleting a comment (comment_id)
    # Option to delete should only show up if the user posted the comment.
    # If the comment has any children, the post should be wiped but still present.
    # If the comment doesn't have any chidlren, the post should be deleted.

    # Log base 10 value of maximum adjacent comment length.
    _N = 10

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(
        get_user_model(),
        on_delete = models.SET_NULL,
        null=True
    )
    likes = models.ManyToManyField(
        get_user_model(),
        on_delete=models.CASCADE,
        help_text="The number of likes a comment gets."
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        help_text=dedent(
            """
        The course with which a comment is associated. Course was chosen instead of topics for
        hosting comments because topics are SOFT STATE and are recomputed regularly.
        """
        )
    )

    parent_id = models.ForeignKey("self")
    path = models.TextField(db_index=True)

    def level(self):
        return len(self.path.split('.'))
    def save(self, **kwargs):
        prefix = self.parent.path + '.' if self.parent else ''
        self.path = prefix + '{:0{}d}'.format(self.id, self._N)
        super().save(**kwargs)
    def delete(self, **kwargs):
        if Comment.objects.filter(parent_id=self).exists():
            self.text = "This comment has been removed."
            self.likes.clear()
            self.author = None
            self.save()
        else:
            super().delete(**kwargs)
    def __str__(self):
        return f"{self.author}: {self.text}"