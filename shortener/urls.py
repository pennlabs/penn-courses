from django.urls import path
from shortener.views import RedirectView

urlpatterns = [
    path('<slug:short>/', RedirectView.as_view(), name='index'),
]
