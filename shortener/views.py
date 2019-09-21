from django.shortcuts import get_object_or_404, redirect
from django.views.generic.base import View
from shortener.models import Url


class RedirectView(View):
    def get(self, request, short):
        url = get_object_or_404(Url, short_id=short)
        return redirect(url.long_url)
