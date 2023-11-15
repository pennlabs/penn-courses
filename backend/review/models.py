from textwrap import dedent
from django.db import models
from django.db.models import Avg, Q, UniqueConstraint, QuerySet
from django.core.exceptions import ObjectDoesNotExist
from backend.review.annotations import annotate_with_matching_reviews
from courses.models import Topic, Instructor, Department
from django.db import transaction

from review.annotations import review_averages, annotate_average_and_recent
from review.views import review_filters_pcr, section_filters_pcr, course_filters_pcr

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
FIELD_SLUGS = [x[2] for x in REVIEW_BIT_LABEL]


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




# Cache Reviews
EXTRA_METRICS_SLUGS = [
    "final_enrollment",
    "percent_open",
    "num_openings",
    "filled_in_adv_reg"
]

SEMESTER_AGGREGATION_SLUGS = [
    "semester_calc",
    "semester_count"
]
ALL_METRIC_SLUGS = FIELD_SLUGS + EXTRA_METRICS_SLUGS + SEMESTER_AGGREGATION_SLUGS
_ALL_METRiC_SLUGS_AVERAGE = [
    "average_" + slug for slug in ALL_METRIC_SLUGS
]
_ALL_METRiC_SLUGS_RECENT = [
    "recent_" + slug for slug in ALL_METRIC_SLUGS
]
_ALL_METRiC_SLUGS_AVERAGE_RECENT = [
    *_ALL_METRiC_SLUGS_AVERAGE,
    *_ALL_METRiC_SLUGS_RECENT
]
                                    

class AverageBit(models.Model):
    """
    Like review.models.ReviewBit, but with only an average field.
    """
    constraints = [
        UniqueConstraint(fields=['field', 'average_reviews'], name='unique_average_bit')
    ]

    field = models.CharField(max_length=32, db_index=True)
    average = models.DecimalField(max_digits=6, decimal_places=5) # TODO: check how n/a values are handled
    count = models.PositiveIntegerField(help="Number of reviews that this average is based on")
    average_review = models.ForeignKey("AverageReview", on_delete=models.CASCADE, related_name='bits', db_index=True) # TODO: add help strings
    average_or_recent = models.BooleanField()


MODEL_MAP = (
    (1, "Topic", Topic),
    (2, "Instructor", Instructor)
    (3, "Department", Department)
)
MODEL_OPTIONS = tuple([(k, v) for k, v, _ in MODEL_MAP])
MODEL_OPTIONS_DICT = {k: v for k, v, _ in MODEL_OPTIONS}
REV_MODEL_OPTIONS_DICT = {v: k for k, v, _ in MODEL_OPTIONS}
MODEL_INDEX_TO_CLASS = {k: v for k, _, v in MODEL_MAP}


class AverageReview(models.Model):
    """
    The reviews for a model (e.g., topic or instructor). 
    This is used to cache the reviews for a given instance of that model. 
    It is expected that subclasses of BaseReviewAverage will be instantiated by a cron job.
    """

    model = models.SmallIntegerField(choices=MODEL_OPTIONS) 
    instance_id = models.PositiveBigIntegerField() # note: this is used to store primary keys, but it supports a 0 value (not supported for primary keys)
    updated_at = models.DateTimeField(auto_now=True, help="Tracks the freshness of the average")

    class Meta:
        constraints = [
            UniqueConstraint(fields=['model', 'instance_id', 'average_or_recent'], name='unique_instructor_average_or_recent')
        ]
        index_together = [
            ['model', 'instance_id', 'average_or_recent']
        ]

    @classmethod
    def get_or_set_average(
        cls,
        model: str,
        instance_id: int,
        average_or_recent_or_both: bool | None
    ) -> QuerySet["AverageBit"]:
        model_index = cls.MODEL_OPTIONS_REV_DICT[model]
        try:
            bits = cls.objects.get(
                model=model_index, 
                instance_id=instance_id
            ).bits.filter(
                Q(average_or_recent=average_or_recent_or_both)
                if average_or_recent_or_both is not None else Q()
            )
            assert len(bits) == len(ALL_METRIC_SLUGS) # TODO: remove in production
            return bits
        except ObjectDoesNotExist:
            return cls.set_average_all(
                model, 
                queryset=MODEL_INDEX_TO_CLASS[model_index].objects.filter(pk=instance_id), 
                average_or_recent_or_both=average_or_recent_or_both
            )


    @classmethod
    def set_averages(
        cls, 
        model: str, 
        queryset: QuerySet[model], 
        average_or_recent_or_both: bool | None
    ):
        """
        Creates and returns averages for all of the items in the queryset.
        :param model: The name of the model to create averages for
        :param queryset: The queryset of instances of `model` to create averages for
        :param average_or_recent: Whether to create averages or recent averages. If None, both are created.
        :return: The queryset of AverageReviews that were created
        """

        # TODO: remove these match statements since prod doesn't support updated python
        match model:
            case "Instructor":
                match_section_on = Q(instructor__in=queryset)
                match_review_on = Q(instructor__in=queryset)
            case "Topic":
                match_section_on = Q(course__topic__in=queryset)
                match_review_on = Q(section__course__topic__in=queryset)
            case "Department":
                match_section_on = Q(course__department__in=queryset)
                match_review_on = Q(section__course__department__in=queryset)

        match average_or_recent_or_both:
            case None:
                fields = _ALL_METRiC_SLUGS_AVERAGE_RECENT
            case True:
                fields = _ALL_METRiC_SLUGS_AVERAGE
            case False:
                fields = _ALL_METRiC_SLUGS_RECENT


        with transaction.atomic():
            if average_or_recent_or_both is None or average_or_recent_or_both:
                queryset = annotate_with_matching_reviews(
                    queryset,
                    match_section_on=match_section_on & section_filters_pcr,
                    match_review_on=match_review_on & review_filters_pcr,
                    most_recent=False,
                    prefix="average_",
                    extra_metrics=True,
                )
            
            if average_or_recent_or_both is None or not average_or_recent_or_both:
                qs = annotate_with_matching_reviews(
                    queryset,
                    match_section_on=match_section_on & section_filters_pcr,
                    match_review_on=match_review_on & review_filters_pcr,
                    most_recent=False,
                    prefix="recent_",
                    extra_metrics=True,
                )
                
            queryset.values(*fields) # TODO: check that this is efficient

            average_reviews = [
                AverageReview.get_or_create( # update averages
                    model=model,
                    instance_id=obj.pk,
                ) 
                for obj in queryset.distinct()
            ]
            
            # create the AverageBit for each reivew
            for field in fields:
                for obj, average_review in zip(qs, average_reviews): # TODO: check that zip is efficient
                    average_or_recent = field.startswith("average_")
                    assert field.startswith("average_") or field.startswith("recent_") # TODO: remove in prod
                    AverageBit.objects.get_or_create(
                        average_review=average_review,
                        field=field,
                        average=obj[field],
                        average_or_recent=average_or_recent
                    )

            return average_reviews