from django.urls import path
from django.views.decorators.cache import cache_page

from review.views import (
    autocomplete,
    course_plots,
    course_reviews,
    department_reviews,
    instructor_for_course_reviews,
    instructor_reviews,
    chat_start,
    chat_message,
    chat_history,
)


HOUR_IN_SECONDS = 60 * 60
DAY_IN_SECONDS = HOUR_IN_SECONDS * 24
MONTH_IN_SECONDS = DAY_IN_SECONDS * 30

urlpatterns = [
    path(
        "course/<slug:course_code>",
        course_reviews,
        name="course-reviews",
    ),
    path(
        "course_plots/<slug:course_code>",
        cache_page(DAY_IN_SECONDS)(course_plots),
        name="course-plots",
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
    path(
        "autocomplete",
        cache_page(MONTH_IN_SECONDS)(autocomplete),
        name="review-autocomplete",
    ),
    path(
        "chat/start",
        chat_start,
        name="chat-start",
    ),
    path(
        "chat/<slug:chat_id>/message",
        chat_message,
        name="chat-message",
    ),
    path(
        "chat/<slug:chat_id>/history",
        chat_history,
        name="chat-history",
    ),
]
