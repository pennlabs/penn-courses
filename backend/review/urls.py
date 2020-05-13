from django.urls import path

from review.views import course_reviews


urlpatterns = [
    path("courses/<slug:course_code>", course_reviews, name="course-reviews"),
]
