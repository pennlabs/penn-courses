from django.urls import include, path

from review.views import course_reviews

urlpatterns = [path("courses/", course_reviews)]
