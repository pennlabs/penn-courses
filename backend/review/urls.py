from django.urls import path
from django.views.decorators.cache import cache_page

from review.views import (
    autocomplete,
    course_reviews,
    department_reviews,
    instructor_for_course_reviews,
    instructor_reviews,
)


MONTH_IN_SECONDS = 60 * 60 * 24 * 30

urlpatterns = [
    path(
        "course/<slug:course_code>",
        cache_page(MONTH_IN_SECONDS)(course_reviews),
        name="course-reviews",
    ),
    path(
        "instructor/<slug:instructor_id>",
        cache_page(MONTH_IN_SECONDS)(instructor_reviews),
        name="instructor-reviews",
    ),
    path(
        "department/<slug:department_code>",
        cache_page(MONTH_IN_SECONDS)(department_reviews),
        name="department-reviews",
    ),
    path(
        "course/<slug:course_code>/<slug:instructor_id>",
        cache_page(MONTH_IN_SECONDS)(instructor_for_course_reviews),
        name="course-history",
    ),
    path("autocomplete", cache_page(MONTH_IN_SECONDS)(autocomplete), name="review-autocomplete"),
]
