from django.urls import path
from django.views.decorators.cache import cache_control, cache_page

from review.views import (
    autocomplete,
    course_reviews,
    department_reviews,
    instructor_for_course_reviews,
    instructor_reviews,
)


HOUR_IN_SECONDS = 60 * 60
DAY_IN_SECONDS = HOUR_IN_SECONDS * 24


def review_cache(fun):
    return cache_control(max_age=0)(cache_page(DAY_IN_SECONDS)(fun))


urlpatterns = [
    path("course/<slug:course_code>", review_cache(course_reviews), name="course-reviews",),
    path(
        "instructor/<slug:instructor_id>",
        review_cache(instructor_reviews),
        name="instructor-reviews",
    ),
    path(
        "department/<slug:department_code>",
        review_cache(department_reviews),
        name="department-reviews",
    ),
    path(
        "course/<slug:course_code>/<slug:instructor_id>",
        review_cache(instructor_for_course_reviews),
        name="course-history",
    ),
    path("autocomplete", cache_page(HOUR_IN_SECONDS)(autocomplete), name="review-autocomplete"),
]
