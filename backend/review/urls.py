from django.urls import path

from review.views import (
    autocomplete,
    course_reviews,
    department_reviews,
    instructor_for_course_reviews,
    instructor_reviews,
)


urlpatterns = [
    path("courses/<slug:course_code>", course_reviews, name="course-reviews"),
    path("instructor/<slug:instructor_id>", instructor_reviews, name="instructor-reviews"),
    path("department/<slug:department_code>", department_reviews, name="department-reviews"),
    path(
        "courses/<slug:course_code>/<slug:instructor_id>",
        instructor_for_course_reviews,
        name="course-history",
    ),
    path("autocomplete", autocomplete, name="review-autocomplete"),
]
