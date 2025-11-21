"""
Materialized Views - Django ORM Approach
=========================================

This is the RECOMMENDED approach. It reuses your existing review_averages() logic
but captures the generated SQL for materialized views.

Key insight: Your review_averages() function already generates the perfect SQL.
We just need to capture it and use it for the materialized view definition.
"""

from django_pgviews import view as pg
from django.db import models


def _get_course_review_sql():
    """
    Generate SQL for course reviews by calling your existing course_reviews() function
    and extracting the SQL it generates.
    """
    from courses.models import Course
    from review.annotations import review_averages
    from review.views import section_filters_pcr
    from django.db.models import Q, OuterRef
    
    # Start with a base queryset
    queryset = Course.objects.all()
    
    # Apply the same review_averages logic as course_reviews()
    queryset = review_averages(
        queryset,
        reviewbit_subfilters=Q(review__section__course__topic=OuterRef("topic")),
        section_subfilters=(section_filters_pcr & Q(course__topic=OuterRef("topic"))),
        fields=['course_quality', 'difficulty', 'instructor_quality', 'work_required'],
        prefix="",
        extra_metrics=False,
    )
    
    # Select only the fields we want in the view
    queryset = queryset.values(
        'id',
        'topic_id', 
        'semester',
        'full_code',
        'title',
        'course_quality',
        'difficulty', 
        'instructor_quality',
        'work_required',
    )
    
    # Get the compiled SQL
    compiler = queryset.query.get_compiler(using=queryset.db)
    sql, params = compiler.as_sql()
    
    # Return just the SQL (django-pgviews handles parameters)
    return sql


def _get_section_review_sql():
    """
    Generate SQL for section reviews by calling sections_with_reviews().
    """
    from courses.models import Section, sections_with_reviews
    
    # Start with base queryset
    queryset = Section.objects.all()
    
    # Apply sections_with_reviews() to get the annotated queryset
    queryset = sections_with_reviews(queryset)
    
    # Select only the fields we want
    queryset = queryset.values(
        'id',
        'course_id',
        'code',
        'course__topic_id',
        'course_quality',
        'difficulty',
        'instructor_quality',
        'work_required',
    )
    
    # Get the compiled SQL
    compiler = queryset.query.get_compiler(using=queryset.db)
    sql, params = compiler.as_sql()
    
    return sql


def _get_recent_course_review_sql():
    """
    Generate SQL for recent course reviews (most recent semester only).
    """
    from courses.models import Course
    from review.annotations import review_averages
    from review.views import section_filters_pcr
    from django.db.models import Q, OuterRef, Subquery, Max, Value
    
    queryset = Course.objects.all()
    
    # Get matching reviews (same logic as course_reviews but filter to recent)
    from review.models import Review
    matching_reviews = Review.objects.filter(
        section__course__topic=OuterRef("course__topic"),
        responses__gt=0
    )
    
    # Get most recent semester
    recent_sem_subquery = Subquery(
        matching_reviews
        .annotate(common=Value(1))
        .values("common")
        .annotate(max_semester=Max("section__course__semester"))
        .values("max_semester")[:1]
    )
    
    # Apply review_averages with recent semester filter
    reviewbit_subfilters = (
        Q(review__section__course__topic=OuterRef("topic"))
        & Q(review__section__course__semester=recent_sem_subquery)
    )
    
    section_subfilters = (
        section_filters_pcr 
        & Q(course__topic=OuterRef("topic"))
        & Q(course__semester=recent_sem_subquery)
    )
    
    queryset = review_averages(
        queryset,
        reviewbit_subfilters=reviewbit_subfilters,
        section_subfilters=section_subfilters,
        fields=['course_quality', 'difficulty', 'instructor_quality', 'work_required'],
        prefix="recent_",
        semester_aggregations=True,
        extra_metrics=False,
    )
    
    queryset = queryset.values(
        'id',
        'topic_id',
        'semester',
        'recent_course_quality',
        'recent_difficulty',
        'recent_instructor_quality',
        'recent_work_required',
        'recent_semester_calc',
        'recent_semester_count',
    )
    
    compiler = queryset.query.get_compiler(using=queryset.db)
    sql, params = compiler.as_sql()
    
    return sql


# ============================================================================
# Materialized View Definitions
# ============================================================================

class CourseReviewMaterialized(pg.MaterializedView):
    """
    Materialized view caching course review averages.
    
    Replicates Course.with_reviews / course_reviews() but as a cached view.
    Refresh with: REFRESH MATERIALIZED VIEW CONCURRENTLY course_review_averages_mv
    """
    
    concurrent_index = 'id'
    
    # Generate SQL using your existing Django ORM logic
    sql = _get_course_review_sql()
    
    # Fields match what's selected in the query
    topic_id = models.IntegerField(null=True)
    semester = models.CharField(max_length=5)
    full_code = models.CharField(max_length=16)
    title = models.TextField()
    
    course_quality = models.FloatField(null=True)
    difficulty = models.FloatField(null=True)
    instructor_quality = models.FloatField(null=True)
    work_required = models.FloatField(null=True)
    
    class Meta:
        managed = False
        db_table = 'course_review_averages_mv'


class SectionReviewMaterialized(pg.MaterializedView):
    """
    Materialized view caching section review averages.
    
    Replicates Section.with_reviews / sections_with_reviews() but as a cached view.
    Refresh with: REFRESH MATERIALIZED VIEW CONCURRENTLY section_review_averages_mv
    """
    
    concurrent_index = 'id'
    
    sql = _get_section_review_sql()
    
    course_id = models.IntegerField()
    code = models.CharField(max_length=16)
    topic_id = models.IntegerField(null=True, db_column='course__topic_id')
    
    course_quality = models.FloatField(null=True)
    difficulty = models.FloatField(null=True)
    instructor_quality = models.FloatField(null=True)
    work_required = models.FloatField(null=True)
    
    class Meta:
        managed = False
        db_table = 'section_review_averages_mv'


class RecentCourseReviewMaterialized(pg.MaterializedView):
    """
    Materialized view caching recent semester course review averages.
    
    Only includes reviews from the most recent semester per topic.
    Refresh with: REFRESH MATERIALIZED VIEW CONCURRENTLY recent_course_review_averages_mv
    """
    
    concurrent_index = 'id'
    
    sql = _get_recent_course_review_sql()
    
    topic_id = models.IntegerField(null=True)
    semester = models.CharField(max_length=5)
    
    recent_course_quality = models.FloatField(null=True)
    recent_difficulty = models.FloatField(null=True)
    recent_instructor_quality = models.FloatField(null=True)
    recent_work_required = models.FloatField(null=True)
    
    recent_semester_calc = models.CharField(max_length=5, null=True)
    recent_semester_count = models.IntegerField(null=True)
    
    class Meta:
        managed = False
        db_table = 'recent_course_review_averages_mv'


# ============================================================================
# Usage Notes
# ============================================================================

"""
After creating these views, use them in your managers:

    from review.materialized_views import (
        CourseReviewMaterialized,
        SectionReviewMaterialized,
        RecentCourseReviewMaterialized,
    )
    
    class OptimizedCourseManager(models.Manager):
        def get_queryset(self):
            qs = super().get_queryset()
            
            # Left join to materialized view
            qs = qs.extra(
                select={
                    'course_quality': 'crm.course_quality',
                    'difficulty': 'crm.difficulty',
                    'instructor_quality': 'crm.instructor_quality',
                    'work_required': 'crm.work_required',
                },
                tables=['course_review_averages_mv crm'],
                where=['crm.id = courses_course.id'],
            )
            
            return qs

Or use annotations with subqueries (shown in materialized_managers.py).
"""