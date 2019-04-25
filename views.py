from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404
from .models import *


def index(request, short):
    matching_url = Url.objects.filter(short_id=short)
    if matching_url.exists():
        return HttpResponseRedirect(matching_url[0].long_url)
    else:
        raise Http404("Shortened URL does not exist")
