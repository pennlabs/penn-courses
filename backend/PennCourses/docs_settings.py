import json
import re
from inspect import getdoc
from textwrap import dedent
from rest_framework import serializers
from django.utils.encoding import force_str
from rest_framework.compat import uritemplate
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.schemas.utils import get_pk_description, is_list_view


"""
This file includes code and settings for our PCx autodocumentation
(based on a Django-generated OpenAPI schema and Redoc, which formats that schema into a
readable documentation web page). Some useful links:
https://github.com/Redocly/redoc
https://github.com/Redocly/redoc/blob/master/docs/redoc-vendor-extensions.md#tagGroupObject
https://www.django-rest-framework.org/api-guide/schemas
https://www.django-rest-framework.org/topics/documenting-your-api/
A Redoc example from which many of the concepts in this file were taken from:
https://redocly.github.io/redoc/
https://github.com/Redocly/redoc/blob/master/demo/openapi.yaml


MAINTENENCE (PLEASE READ IN FULL):
For the auto-documentation to work, you need to include the line:
schema = PcxAutoSchema()
in all views (this will allow for proper tag and operation_id generation; see below).
PcxAutoSchema (defined below) is a subclass of Django's AutoSchema, and it makes some improvements
on that class for use with Redoc as well as some customizations specific to the Labs PCX use-case.
You should include docstrings in views (see
https://www.django-rest-framework.org/coreapi/from-documenting-your-api/#documenting-your-views)
explaining the function of the view (or of each method if there are multiple supported methods).
If the meaning of a tag group created automatically by the docs
(visible in the nav bar) is not clear, you should add a custom description.
You can do that using the custom_tag_descriptions dictionary below.
If any auto-generated names are unsatisfactory, you can also manually change any
operation_id, tag, or tag group name (see below for more on what these are).
You can update the introductory sections / readme by editing the markdown-formatted
openapi_description text below.
When writing any class-based views where you specify a queryset (such as ViewSets), even if you
override get_queryset(), you should also specify the queryset field with something like
queryset = ExampleModel.objects.none() (using .none() to prevent accidental data breach), or alternatively 
a sensible queryset default (e.g. queryset = Course.with_reviews.all() for the CourseDetail ViewSet). 
Basically, just make sure the queryset parameter is always pointing to the relevant model 
(if you are using queryset or get_queryset()). This will allow the auto-documentation to access the model 
underlying the queryset (it cannot call get_queryset() since it cannot generate a request object which 
the get_queryset() method might try to access). If the meaning of a model or serializer field is not clear, 
you should include the string help_text as a parameter when initializing the field, explaining what that 
field stores. This will show up in the documentation such that parameter descriptions are inferred from
model or serializer field help text. For properties, the docstring will be used since there is no
way to define help_text for a property; so even if a property's use is clear based on the code,
keep in mind that describing it's purpose in the docstring will be helpful to frontend engineers
who are unfamiliar with the backend code (also, don't include a :return: tag as you might normally
do for functions; a property is to be treated as a dynamic field, not a method, so just state
what the method returns as the only text in the docstring).
Including help_text/docstring when a field/property's purpose is unclear will also
make the model/serializer code more understandable for newbies. And furthermore, all help_text
and descriptive docstrings will not only help future Labs developers but it will also show up in
the backend documentation (accessible at /admin/doc/).
"""

openapi_description = """
# Introduction
Penn Courses ([GitHub](https://github.com/pennlabs/penn-courses">)) is the umbrella
categorization for [Penn Labs](https://pennlabs.org/)
products designed to help students navigate the course registration process. It currently
includes three products, each with their own API documented on this page:
Penn Course Alert, Penn Course Plan, and Penn Course Review (PCR coming soon).

See `Penn Labs Notion > Penn Courses` for more details on each of our (currently) three apps.

For instructions on how to maintain this documentation while writing code,
see the comments in `backend/PennCourses/docs_settings.py` (it is easy, and will be helpful
for maintaining Labs knowledge in spite of our high member turnover rate).

See our
[GitHub](https://github.com/pennlabs/penn-courses">) repo for instructions on
installation, running in development, and loading in course data for development. Visit
the `/admin/doc/` route ([link](/admin/doc/)) for the backend documentation (admin account required,
which can be made by running `python manage.py createsuperuser` in terminal/CLI).

# Unified Penn Courses
By virtue of the fact that all Penn Courses products deal with, well, courses,
it would make sense for all three products to share the same backend.

We realized the necessity of a unified backend when attempting to design a new Django backend
for Penn Course Plan. We like to live by the philosophy of keeping it
[DRY](https://en.wikipedia.org/wiki/Don't_repeat_yourself), and
PCA and PCP's data models both need to reference course and
section information. We could have simply copied over code (a bad idea)
or created a shared reusable Django app (a better idea) for course data,
but each app would still need to download copies of the same data.
Additionally, this will help us build integrations between our Courses products.

See `Penn Labs Notion > Penn Courses > Unified Penn Courses` for more details on our
codebase file structure, data models, and multi-site devops scheme.

# Authentication
Currently, PCx user authentication is taken care of by platform's Penn Labs Accounts system.
See `Penn Labs Notion > Platform > The Accounts Engine` for extensive documentation and
links to repositories for this system. When tags or routes are described as requiring user
authentication, they are referring to this system. See the Django docs for more on Django's
[User Authentication system](https://docs.djangoproject.com/en/3.0/topics/auth/),
with underlies, PLA.
"""

subpath_abbreviations = {"plan": "PCP", "alert": "PCA", "review": "PCR", "courses": "PCx"}

# tag groups organize tags into groups; we are using them to separate our tags by app
tag_group_abbreviations = {
    "PCP": "Penn Course Plan",
    "PCA": "Penn Course Alert",
    "PCR": "Penn Course Review",
    "PCx": "Penn Courses (Unified)",
}


# operation ids are the subitems of a tag (if you click on a tag you see them)
# tags show up in the body of the documentation and as "sections" in the menu
# tags are not to be confused with tag groups (see above description of tag groups)

# name here refers to the name underlying the operation id of the view
# this is NOT the name that you see on the API, it is the name underlying it,
# and is used in construction of that name (see below get_name
# and _get_operation_id methods in PcxAutoSchema for an explanation of the difference). The name
# also defines what the automatically-set tag name will be.
custom_name = {  # keys are (path, method) tuples, values are custom names
    # method is one of ("GET", "POST", "PUT", "PATCH", "DELETE")
    ("/api/alert/registrationhistory/", "GET"): "Registration History",
    ("/api/alert/registrationhistory/{id}/", "GET"): "Registration History",
}

custom_operation_id = {  # keys are (path, method) tuples, values are custom names
    # method is one of ("GET", "POST", "PUT", "PATCH", "DELETE")
    ("/api/alert/registrationhistory/", "GET"): "List Registration History",
}

# Use this dictionary to
# The default response code to use in Django's OpenAPI AutoSchema is 200
# When this default is undesirable, you can change it below.
change_response_code = {  # keys are (path, method) tuples, values are custom names
    # method is one of ("GET", "POST", "PUT", "PATCH", "DELETE")
    # value should be a tuple of the form: (old_code, new_code)
    ("/api/plan/schedules/{id}/", "PUT"): (),
}

# Use this dictionary to rename tags, if you wish to do so
# keys are old tag names (seen on docs), values are new tag names
custom_tag_names = {}

# tag descriptions show up in the documentation below the tag name
custom_tag_descriptions = {
    # keys are tag names (after any name changes from above dicts), vals are descriptions
    "[PCP] Schedule": dedent(
        """
    These routes allow interfacing with the user's PCP Schedules for the current semester,
    stored on the backend. Ever since we integrated Penn Labs Accounts into PCP so that users
    can store their schedules across devices and browsers, we have stored users' schedules on
    our backend (rather than local storage).
    <span style="color:red;">User authentication required</span> for all routes.
    """
    ),
    "[PCP] Requirements": dedent(
        """
    These routes expose the academic requirements for the current semester which are stored on
    our backend (hopefully comprehensive). Authentication not required.
    """
    ),
    "[PCP] Course": dedent(
        """
    These routes expose course information for PCP for the current semester.  Authentication not
    required.
    """
    ),
    "[PCA] Registration History": dedent(
        """
    These routes expose a user's registration history (including deleted registrations)
    for the current semester. <span style="color:red;">User authentication required</span>
    for all routes.
    """
    ),
    "[PCA] Registration": dedent(
        """
        These routes expose a user's alert registrations
        for the current semester. <span style="color:red;">User authentication required</span>
        for all routes.
        """
    ),
    "[PCA] User": dedent(
        """
    These routes expose a user's saved settings. 
    <span style="color:red;">User authentication required</span> for all routes.
    """
    ),
    "[PCA] Sections": dedent(
        """
    This route is used by PCA to get data about sections.
    """
    ),
}

# do not edit
labs_logo = (
    "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZ"
    "pZXdCb3g9Ii01MCAtNTAgNDIxLjAxIDIyNS42NyI+PGRlZnM+PHN0eWxlPi5jbHMtMXtmaWxsOiMxMjI3"
    "NGI7fS5jbHMtMntmaWxsOiMyMDljZWU7fTwvc3R5bGU+PC9kZWZzPjx0aXRsZT5sYWJzLWZ1bGwtbG9nb"
    "zwvdGl0bGU+PGcgaWQ9IkxheWVyXzIiIGRhdGEtbmFtZT0iTGF5ZXIgMiI+PGcgaWQ9IkxheWVyXzEtMi"
    "IgZGF0YS1uYW1lPSJMYXllciAxIj48cGF0aCBjbGFzcz0iY2xzLTEiIGQ9Ik0xNzcuMzcsNi4xMXE1LDQ"
    "uNCw1LDEyLjA4dC01LDEycS01LDQuMzYtMTMuNTYsNC4zNkgxNTIuMDVWNTQuNTFoLTguNTZWMS43MWgy"
    "MC4zMlExNzIuMzcsMS43MSwxNzcuMzcsNi4xMVpNMTcwLjc3LDI1cTIuNzItMi4yOCwyLjcyLTYuODQsM"
    "C05LjItMTEtOS4yaC0xMC40VjI3LjMxaDEwLjRRMTY4LjA1LDI3LjMxLDE3MC43NywyNVoiLz48cGF0aC"
    "BjbGFzcz0iY2xzLTEiIGQ9Ik0yMjYsMzcuNzFIMTk2LjY5cS43Miw1LjI4LDMuNzYsOGExMS4yMSwxMS4"
    "yMSwwLDAsMCw3Ljg0LDIuNzYsMTMuNjMsMTMuNjMsMCwwLDAsNi41Mi0xLjQsNy4zMiw3LjMyLDAsMCww"
    "LDMuNTYtNGw3LjEyLDNxLTQuNDgsOS4yOC0xNy4yLDkuMjgtOS40NCwwLTE0Ljc2LTUuNTJ0LTUuMzItM"
    "TUuMjhxMC05Ljg0LDUuMTItMTUuMzJ0MTQuNC01LjQ4cTguOCwwLDEzLjY4LDUuMzZ0NC44OCwxNC4yNE"
    "EyOSwyOSwwLDAsMSwyMjYsMzcuNzFaTTIwMC4yNSwyMy4yM3EtMi44NCwyLjcyLTMuNTYsNy45MmgyMS4"
    "2YTEzLjE4LDEzLjE4LDAsMCwwLTMuNC03Ljg0LDkuNjIsOS42MiwwLDAsMC03LjE2LTIuOEExMC4zNywx"
    "MC4zNywwLDAsMCwyMDAuMjUsMjMuMjNaIi8+PHBhdGggY2xhc3M9ImNscy0xIiBkPSJNMjY4LjMzLDE3L"
    "jU1cTQuMiwzLjg0LDQuMiwxMVY1NC41MUgyNjRWMzEuMzFxMC0xMC41Ni04LjU2LTEwLjU2YTEwLjY4LD"
    "EwLjY4LDAsMCwwLTcuNjgsMy4wOHEtMy4yLDMuMDgtMy4yLDkuNDh2MjEuMkgyMzZ2LTQwaDcuNmwuNCw"
    "2LjY0YTEzLDEzLDAsMCwxLDUuNTItNS42LDE3LDE3LDAsMCwxLDgtMS44NEExNS40NCwxNS40NCwwLDAs"
    "MSwyNjguMzMsMTcuNTVaIi8+PHBhdGggY2xhc3M9ImNscy0xIiBkPSJNMzE2LjgxLDE3LjU1cTQuMiwzL"
    "jg0LDQuMiwxMVY1NC41MWgtOC41NlYzMS4zMXEwLTEwLjU2LTguNTYtMTAuNTZhMTAuNjgsMTAuNjgsMC"
    "wwLDAtNy42OCwzLjA4cS0zLjIsMy4wOC0zLjIsOS40OHYyMS4yaC04LjU2di00MGg3LjZsLjQsNi42NGE"
    "xMywxMywwLDAsMSw1LjUyLTUuNiwxNywxNywwLDAsMSw4LTEuODRBMTUuNDQsMTUuNDQsMCwwLDEsMzE2"
    "LjgxLDE3LjU1WiIvPjxwYXRoIGNsYXNzPSJjbHMtMSIgZD0iTTE4MS41MiwxMTcuNTF2Ny4zNkgxNDMuO"
    "DRWNzIuMDdoOC41NnY0NS40NFoiLz48cGF0aCBjbGFzcz0iY2xzLTEiIGQ9Ik0yMjguMDgsMTE4Ljk1bC"
    "0uNTYsNS43NmExMi4xLDEyLjEsMCwwLDEtNSwxLDkuNzUsOS43NSwwLDAsMS01LjQ4LTEuMzYsNi43Niw"
    "2Ljc2LDAsMCwxLTIuNjgtNC41NiwxMiwxMiwwLDAsMS01LjQ0LDQuMzYsMjAuMTIsMjAuMTIsMCwwLDEt"
    "OC4wOCwxLjU2LDE1LjI1LDE1LjI1LDAsMCwxLTkuNDQtMi43Miw5LjE1LDkuMTUsMCwwLDEtMy42LTcuN"
    "zYsMTAsMTAsMCwwLDEsMy45Mi04cTMuOTItMy4yNCwxMS42OC00LjZsMTAuMTYtMS43NlY5OC43MWE3Lj"
    "c2LDcuNzYsMCwwLDAtMi4xNi01LjgsOC4yMSw4LjIxLDAsMCwwLTYtMi4xMnEtNy45MiwwLTEwLjMyLDc"
    "uMmwtNi42NC0zLjUyYTEzLjI5LDEzLjI5LDAsMCwxLDUuODgtNy42LDIwLjA4LDIwLjA4LDAsMCwxLDEw"
    "LjkyLTIuOHE3Ljc2LDAsMTIuMzIsMy42dDQuNTYsMTAuNTZ2MTguMDhhMy4xNywzLjE3LDAsMCwwLC42O"
    "CwyLjI0LDMsMywwLDAsMCwyLjI4LjcyQTExLjY1LDExLjY1LDAsMCwwLDIyOC4wOCwxMTguOTVabS0xNy"
    "43Ni0xLjg0YTYuMyw2LjMsMCwwLDAsMy4yOC01LjUydi00LjhsLTguNzIsMS43NmExNS45MiwxNS45Miw"
    "wLDAsMC02LjE2LDIuMjQsNC41LDQuNSwwLDAsMC0yLDMuODQsNCw0LDAsMCwwLDEuNTYsMy40LDcuMzMs"
    "Ny4zMywwLDAsMCw0LjQ0LDEuMTZBMTMuODgsMTMuODgsMCwwLDAsMjEwLjMyLDExNy4xMVoiLz48cGF0a"
    "CBjbGFzcz0iY2xzLTEiIGQ9Ik0yNzAuNjQsODkuNjNxNC43Miw1LjU2LDQuNzIsMTUuMzJ0LTQuNzIsMT"
    "UuMjRxLTQuNzIsNS40OC0xMyw1LjQ4YTE1LjIxLDE1LjIxLDAsMCwxLTguMjgtMi4yNCwxMy45MywxMy4"
    "5MywwLDAsMS01LjMyLTZsLS40LDcuNDRoLTcuNTJ2LTU4aDguNTZ2MjQuNEExMy4yOSwxMy4yOSwwLDAs"
    "MSwyNTAsODZhMTUuNDIsMTUuNDIsMCwwLDEsNy43Mi0xLjkyUTI2NS45Miw4NC4wNywyNzAuNjQsODkuN"
    "jNabS02Ljc2LDI1LjQ4cTIuOTItMy42OCwyLjkyLTEwLjI0dC0yLjkyLTEwLjJBMTAuOSwxMC45LDAsMC"
    "wwLDI0OCw5NC4zMXEtMi45MiwzLjI4LTMuMjQsOXYzcS4zMiw1Ljg0LDMuMjQsOS4xMmE5LjkyLDkuOTI"
    "sMCwwLDAsNy44LDMuMjhBOS43OSw5Ljc5LDAsMCwwLDI2My44OCwxMTUuMTFaIi8+PHBhdGggY2xhc3M9"
    "ImNscy0xIiBkPSJNMjkwLjIsMTIzLjU5YTE0Ljc4LDE0Ljc4LDAsMCwxLTcuMDgtNi4zMmw1Ljc2LTVhO"
    "S45LDkuOSwwLDAsMCw0LjcyLDUsMTcsMTcsMCwwLDAsNy42OCwxLjYsMTIuNTMsMTIuNTMsMCwwLDAsNi"
    "4zMi0xLjMyLDQsNCwwLDAsMCwyLjI0LTMuNDgsMy40NywzLjQ3LDAsMCwwLTIuMDgtMy4wOCwyNy40Miw"
    "yNy40MiwwLDAsMC03LjItMi4ycS04Ljg4LTEuNjgtMTIuNDgtNC40OGE5LjQ1LDkuNDUsMCwwLDEtMy42"
    "LTcuOTIsMTAuNDIsMTAuNDIsMCwwLDEsMi02LjEyLDEzLjg5LDEzLjg5LDAsMCwxLDUuOC00LjU2LDIxL"
    "jY4LDIxLjY4LDAsMCwxLDktMS43MnE2LjY0LDAsMTAuNjQsMi4yYTE0LjQ5LDE0LjQ5LDAsMCwxLDYuMT"
    "YsNi44NEwzMTIsOTcuNTlhMTAuNiwxMC42LDAsMCwwLTQtNS4xNiwxMi4xOSwxMi4xOSwwLDAsMC02LjY"
    "tMS42NCwxMSwxMSwwLDAsMC02LDEuNDhRMjkzLDkzLjc1LDI5Myw5NS42N2EzLjg4LDMuODgsMCwwLDAs"
    "Mi4xMiwzLjQ0cTIuMTIsMS4yOCw3LjcyLDIuMzIsOC40OCwxLjUyLDEyLDQuMzJhOS40NSw5LjQ1LDAsM"
    "CwxLDMuNTIsNy44NCwxMC4zMSwxMC4zMSwwLDAsMS00LjY0LDguNzJxLTQuNjQsMy4zNi0xMi44LDMuMz"
    "ZBMjYuMjYsMjYuMjYsMCwwLDEsMjkwLjIsMTIzLjU5WiIvPjxwYXRoIGNsYXNzPSJjbHMtMSIgZD0iTTM"
    "wLjQyLDExMi4zNXEzLjEzLDIsMTAsMkwzOSwxMjQuNzNxLTEyLjkxLDAtMTguNS00LjQ2dC01LjU5LTEz"
    "LjkxVjgxLjczcTAtNy40NS0zLjM5LTEwLjY1VDAsNjcuODlWNTdxOC4xMiwwLDExLjUxLTMuMTl0My4zO"
    "S0xMC42NVYxOC4zN3EwLTkuNDUsNS41OS0xMy45MVQzOSwwbDEuNDYsMTAuMzhxLTYuOTIsMC0xMCwyYT"
    "YuODksNi44OSwwLDAsMC0zLjEzLDYuMjZWNDUuMTNxMCwxMy41OC0xNC43OCwxNy4zMVEyNy4yOSw2NS4"
    "4OSwyNy4yOSw3OS42djI2LjQ5QTYuODksNi44OSwwLDAsMCwzMC40MiwxMTIuMzVaIi8+PHBhdGggY2xh"
    "c3M9ImNscy0xIiBkPSJNMTEwLjkxLDUzLjc4UTExNC4zLDU3LDEyMi40Miw1N1Y2Ny44OXEtOC4xMiwwL"
    "TExLjUxLDMuMTl0LTMuMzksMTAuNjV2MjQuNjNxMCw5LjQ1LTUuNTksMTMuOTF0LTE4LjUsNC40Nkw4Mi"
    "wxMTQuMzVxNi45MiwwLDEwLTEuOTNUOTUsMTA2LjA5Vjc5LjZxMC0xMy43MSwxNC43OC0xNy4xN1E5NSw"
    "1OC43MSw5NSw0NS4xM1YxOC42NGE2LjkzLDYuOTMsMCwwLDAtMy4wNi02LjI2cS0zLjA2LTItMTAtMkw4"
    "My40MiwwcTEyLjkxLDAsMTguNSw0LjQ2dDUuNTksMTMuOTFWNDMuMTNRMTA3LjUyLDUwLjU5LDExMC45M"
    "Sw1My43OFoiLz48Y2lyY2xlIGNsYXNzPSJjbHMtMiIgY3g9IjcxLjY3IiBjeT0iMzMuNjkiIHI9IjUuNz"
    "kiLz48Y2lyY2xlIGNsYXNzPSJjbHMtMiIgY3g9IjYxLjA4IiBjeT0iMTAuMjkiIHI9IjUuNzkiLz48Y2l"
    "yY2xlIGNsYXNzPSJjbHMtMiIgY3g9IjUwLjUzIiBjeT0iNDguNyIgcj0iNS43OSIvPjxwYXRoIGNsYXNz"
    "PSJjbHMtMiIgZD0iTTc3LjI2LDYzSDQ1YTcuNDcsNy40NywwLDAsMC03LjQ3LDcuNDdWOTkuMzdBNy40N"
    "yw3LjQ3LDAsMCwwLDQ1LDEwNi44NEg3Ny4yNmE3LjQ3LDcuNDcsMCwwLDAsNy40Ny03LjQ3VjcwLjUxQT"
    "cuNDcsNy40NywwLDAsMCw3Ny4yNiw2M1pNNzEsODIuMzRhNS43OSw1Ljc5LDAsMSwxLDUuOTMtNS42NEE"
    "1Ljc5LDUuNzksMCwwLDEsNzEsODIuMzRaIi8+PC9nPjwvZz48L3N2Zz4="
)


def split_camel(w):
    return re.sub("([a-z0-9])([A-Z])", lambda x: x.groups()[0] + " " + x.groups()[1], w)


def pluralize_word(s):
    return s + "s"  # naive solution because this is how it is done in DRF


def make_manual_schema_changes(data):
    """
    Use this space to make manual modifications to the schema before it is
    presented to the user. Only make manual changes as a last resort, and try
    to use built-in functionality whenever possible.
    These modifications were written by referencing the existing schema at /api/openapi
    and also an example schema (written in YAML instead of JSON, but still
    easily interpretable as JSON) from a Redoc example:
    https://github.com/Redocly/redoc/blob/master/demo/openapi.yaml
    """

    data["info"]["x-logo"] = {"url": labs_logo, "altText": "Labs Logo"}
    data["info"]["contact"] = {"email": "contact@pennlabs.org"}

    # Remove ID from the documented PUT request body for /api/plan/schedules/
    # (the id field in the request body is ignored in favor of the id path parameter)
    for content_ob in data["paths"]["/api/plan/schedules/{id}/"]["put"]["requestBody"]["content"].values():
        content_ob["schema"]["properties"].pop('id', None)

    # Make the id and semester fields show up in PCP schedule request body under sections
    # (and make id required)
    for path, path_ob in data["paths"].items():
        if "plan/schedules" not in path:
            continue
        for method_ob in path_ob.values():
            if "requestBody" not in method_ob.keys():
                continue
            for content_ob in method_ob["requestBody"]["content"].values():
                properties_ob = content_ob["schema"]["properties"]
                if "sections" in properties_ob.keys():
                    section_ob = properties_ob["sections"]
                    if "required" not in section_ob["items"].keys():
                        section_ob["items"]["required"] = []
                    section_ob["items"]["required"].append("id")
                    section_ob["items"]["required"].append("semester")
                    for field, field_ob in section_ob["items"]["properties"].items():
                        if field == "id" or field == "semester":
                            field_ob["readOnly"] = False
                        if field == "id":
                            field_ob["readOnly"] = False

    # Make application/json the only content type
    def delete_other_content_types_dfs(dictionary):
        if not isinstance(dictionary, dict):
            return None
        dictionary.pop('application/x-www-form-urlencoded', None)
        dictionary.pop('multipart/form-data', None)
        for value in dictionary.values():
            delete_other_content_types_dfs(value)
    delete_other_content_types_dfs(data)


examples_dict = {}  # populated by PcxAutoSchema instantiations


class JSONOpenAPICustomTagGroupsRenderer(JSONOpenAPIRenderer):
    def render(self, data, media_type=None, renderer_context=None):
        """
        This overridden method modifies the JSON OpenAPI schema generated by Django
        to add tag groups, and most of the other customization specified above.
        It was written by referencing the existing schema at /api/openapi
        and also an example schema (written in YAML instead of JSON, but still
        easily interpretable as JSON) from a Redoc example:
        https://github.com/Redocly/redoc/blob/master/demo/openapi.yaml
        """

        global examples_dict
        for key, val in examples_dict.items():
            examples_dict[key] = {k.lower(): v for k, v in examples_dict[key].items()}
            for val2 in examples_dict[key].values():
                if "responses" in val2.keys():
                    for res in val2["responses"]:
                        if "code" in res.keys() and isinstance(res["code"], int):
                            res["code"] = str(res["code"])

        tags = set()
        tag_to_dicts = dict()
        for x in data["paths"].values():
            for v in x.values():
                if "tags" in v.keys():
                    tags.update(v["tags"])
                    for t in v["tags"]:
                        if t not in tag_to_dicts.keys():
                            tag_to_dicts[t] = []
                        tag_to_dicts[t].append(v)
        changes = dict()

        def update_tag(old_tag, new_tag):
            for val in tag_to_dicts[old_tag]:
                val["tags"] = [(t if t != old_tag else new_tag) for t in val["tags"]]
            lst = tag_to_dicts.pop(old_tag)
            tag_to_dicts[new_tag] = lst
            changes[old_tag] = new_tag  # since tags cannot be updated while iterating through tags
            return new_tag

        for tag in tags:
            tag = update_tag(tag, split_camel(tag))
            all_list = all([("list" in v["operationId"].lower()) for v in tag_to_dicts[tag]])
            if all_list:  # if all views in tag are lists, pluralize tag name
                tag = update_tag(
                    tag, " ".join(tag.split(" ")[:-1] + [pluralize_word(tag.split(" ")[-1])])
                )
            if tag in custom_tag_names.keys():  # rename custom tags
                tag = update_tag(tag, custom_tag_names[tag])

        for path_name, val in data["paths"].items():  # Display the method and path more visibly
            for method_name, v in val.items():
                v["description"] = (
                    "("
                    + method_name.upper()
                    + " `"
                    + path_name
                    + "`)"
                    + "  \n  \n"
                    + v["description"]
                )

                # remove 'required' tags from responses
                # (it doesn't make sense for a response item to be 'required')
                def delete_required_dfs(dictionary):
                    if not isinstance(dictionary, dict):
                        return None
                    dictionary.pop('required', None)
                    for value in dictionary.values():
                        delete_required_dfs(value)
                delete_required_dfs(v['responses'])


        for k, v in changes.items():  # since tags cannot be updated while iterating through tags
            tags.remove(k)
            tags.add(v)

        data["tags"] = [
            {"name": tag, "description": custom_tag_descriptions.get(tag, "")} for tag in tags
        ]
        data["x-tagGroups"] = [
            {"name": v, "tags": [t for t in tags if k in t]}
            for k, v in tag_group_abbreviations.items()
        ]
        data["x-tagGroups"] = [g for g in data["x-tagGroups"] if len(g["tags"]) != 0]

        for path in examples_dict.keys():
            for method in examples_dict[path].keys():
                ob = examples_dict[path][method]
                if path not in data["paths"].keys():
                    raise ValueError(f"Check your examples file for:\n{method} {path}\n"
                                     "no such path exists in schema")
                if method not in data["paths"][path].keys():
                    raise ValueError(f"Check your examples file for:\n{method} {path}\n"
                                     "no such method exists for the given path")
                if "responses" in ob.keys():
                    for response in ob["responses"]:
                        if "code" not in response.keys():
                            raise ValueError(f"Check your examples file for:\n{method} {path}\n"
                                             "an object in the responses list does not contain "
                                             "a response code key/value pair.")
                        code = response["code"]
                        if "responses" not in data["paths"][path][method].keys():
                            raise ValueError(f"Check your examples file for:\n{method} {path}\n"
                                             "the given path and method does not have a responses "
                                             "object in the schema, but an example response was given.")
                        if code not in data["paths"][path][method]["responses"].keys():
                            raise ValueError(f"Check your examples file for:\n{method} {path}\n"
                                             f"an example response with code {code} is invalid "
                                             "because that is not a response code in the schema "
                                             "for the given path/method.")
                        if "content" not in data["paths"][path][method]["responses"][code].keys():
                            raise ValueError(f"Check your response_codes dictionary for:\n"
                                             f"{method.upper()} {path}, response code {code}\n"
                                             f"If '[DEFAULT]' is not in the description for this path/method/code, "
                                             "no response schema content will be created for it "
                                             "and you will not be able to make an example response for it. "
                                             f"Alternatively, remove the {code} response from "
                                             f"the {method.upper()} {path} responses list in your examples dict.")
                        if "application/json" not in data["paths"][path][method]["responses"][code]["content"].keys():
                            raise ValueError(f"Check your examples file for:\n{method} {path}\n"
                                             f"an example response with code {code} is invalid "
                                             "because the response corresponding to the given "
                                             "path/method/code does not have data type application/json.")
                        final_ob = data["paths"][path][method]["responses"][code]["content"]["application/json"]
                        if "examples" not in final_ob.keys():
                            final_ob["examples"] = {}
                        if "summary" not in response.keys():
                            raise ValueError(f"Check your examples file for:\n{method} {path}\n"
                                             f"an example response with code {code} is invalid "
                                             "because it does not contain required field 'summary'.")
                        if "value" not in response.keys():
                            raise ValueError(f"Check your examples file for:\n{method} {path}\n"
                                             f"an example response with code {code} is invalid "
                                             "because it does not contain required field 'value'.")
                        final_ob["examples"][response["summary"]] = response
                if "requests" in ob.keys():
                    for request in ob["requests"]:
                        if "requestBody" not in data["paths"][path][method].keys():
                            raise ValueError(f"Check your examples file for:\n{method} {path}\n"
                                             "the given path and method does not have a requestBody "
                                             "object in the schema, but an example request was given.")
                        if "application/json" not in data["paths"][path][method]["requestBody"]["content"].keys():
                            raise ValueError(f"Check your examples file for:\n{method} {path}\n"
                                             f"an example request is invalid "
                                             "because the request corresponding to the given "
                                             "path/method/code does not have data type application/json.")
                        final_ob = data["paths"][path][method]["requestBody"]["content"]["application/json"]
                        if "examples" not in final_ob.keys():
                            final_ob["examples"] = {}
                        if "summary" not in request.keys():
                            raise ValueError(f"Check your examples file for:\n{method} {path}\n"
                                             f"an example request is invalid "
                                             "because it does not contain required field 'summary'.")
                        if "value" not in request.keys():
                            raise ValueError(f"Check your examples file for:\n{method} {path}\n"
                                             f"an example request is invalid "
                                             "because it does not contain required field 'value'.")
                        final_ob["examples"][request["summary"]] = request

        make_manual_schema_changes(data)

        return json.dumps(data, indent=2).encode("utf-8")


class PcxAutoSchema(AutoSchema):
    """
    This custom subclass serves to automatically generate tags and operation ID in forms
    better for Redoc and our PCX usecase.
    It also serves to backport code for custom tags generation functionality from
    this DRF PR (which hadn't been included in a stable release when this code was written):
    https://github.com/encode/django-rest-framework/pull/7184/files
    This PR is adding the functionality outlined here in the DRF api guide:
    https://www.django-rest-framework.org/api-guide/schemas/#grouping-operations-with-tags
    Once the code from this PR is included in a stable Django release, the get_operation methods below
    should be deleted (it will be inherited from AutoSchema) and the tag code should be removed from __init__.
    """

    def __init__(self, tags=None, examples={}, response_codes={}):
        global examples_dict
        """
            Parameters:

            * `tags`: list of strings (tags) which will override the auto-generation of tags
        """
        if tags and not all(isinstance(tag, str) for tag in tags):
            raise ValueError("tags must be a list or tuple of string.")
        self._tags = tags

        for k, d in response_codes.items():
            response_codes[k] = {k.upper(): v for k, v in d.items()}
        self.response_codes = response_codes

        examples_dict.update(examples)

        super().__init__()

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation["tags"] = self.get_tags(path, method)
        return operation

    def get_action(self, path, method):  # Code taken from _get_operation_id method
        method_name = getattr(self.view, "action", method.lower())
        if is_list_view(path, method, self.view):
            action = "list"
        elif method_name not in self.method_mapping:
            action = method_name
        else:
            action = self.method_mapping[method.lower()]
        return action

    def get_name(self, path, method):  # Some code taken from _get_operation_id method
        if (path, method) in custom_name.keys():
            return custom_name[(path, method)]

        # Try to deduce the ID from the view's model
        model = getattr(getattr(self.view, "queryset", None), "model", None)
        if model is not None:
            name = model.__name__

        # Try with the serializer class name
        elif hasattr(self.view, "get_serializer_class"):
            name = self.view.get_serializer_class().__name__
            if name.endswith("Serializer"):
                name = name[:-10]

        # Fallback to the view name
        else:
            name = self.view.__class__.__name__
            if name.endswith("APIView"):
                name = name[:-7]
            elif name.endswith("View"):
                name = name[:-4]
            elif name.lower().endswith("viewset"):
                name = name[:-7]

        # Due to camel-casing of classes and `action` being lowercase,
        # apply title in order to find if action truly comes at the end of the name
        if name.endswith(
            self.get_action(path, method).title()
        ):  # ListView, UpdateAPIView, ThingDelete ...
            name = name[: -len(self.get_action(path, method))]

        return name

    def get_tags(self, path, method):
        # If user has specified tags, use them.
        if self._tags:
            return self._tags

        name = self.get_name(path, method)
        path_components = (path[1:] if path.startswith("/") else path).split("/")
        return [
            (
                "[" + subpath_abbreviations[path_components[1]] + "] "
                if path_components[1] in subpath_abbreviations.keys()
                else ""
            )
            + name
        ]

    def _get_operation_id(self, path, method):
        if (path, method) in custom_operation_id.keys():
            return custom_operation_id[(path, method)]

        action = self.get_action(path, method)
        name = self.get_name(path, method)

        if action == "list":  # listThings instead of listThing
            name = pluralize_word(name)

        ret = action + name

        return split_camel(ret[0].capitalize() + ret[1:])

    def _get_path_parameters(self, path, method):
        """
        Return a list of parameters from templated path variables.
        """
        assert uritemplate, "`uritemplate` must be installed for OpenAPI schema support."

        model = getattr(getattr(self.view, "queryset", None), "model", None)
        parameters = []

        for variable in uritemplate.variables(path):
            description = ""
            if model is not None:  # TODO: test this.
                # Attempt to infer a field description if possible.
                try:
                    model_field = model._meta.get_field(variable)
                except Exception:
                    model_field = None

                if model_field is not None and model_field.help_text:
                    description = force_str(model_field.help_text)
                elif model_field is not None and model_field.primary_key:
                    description = get_pk_description(model, model_field)

                if (
                    model_field is None
                    and variable in model.__dict__.keys()
                    and isinstance(model.__dict__[variable], property)
                ):
                    doc = getdoc(model.__dict__[variable])
                    description = "" if doc is None else doc

                if not description or "A unique integer value" in description and variable == "id":
                    description = f"The id of the {str(model.__name__).lower()}."

            parameter = {
                "name": variable,
                "in": "path",
                "required": True,
                "description": description,
                "schema": {"type": "string",},  # TODO: integer, pattern, ...
            }
            parameters.append(parameter)

        return parameters

    def _get_responses(self, path, method):
        # TODO: Handle multiple codes and pagination classes.
        if method == 'DELETE':
            if (
                path not in self.response_codes.keys() or
                method not in self.response_codes[path].keys() or
                not self.response_codes[path][method]
            ):
                return {
                    '204': {
                        'description': ''
                    }
                }
            return {
                str(k): {'description': v.replace("[DEFAULT]", "")}
                for k, v in self.response_codes[path][method].items()
            }

        self.response_media_types = self.map_renderers(path, method)

        item_schema = {}
        serializer = self._get_serializer(path, method)

        if isinstance(serializer, serializers.Serializer):
            item_schema = self._map_serializer(serializer)
            # No write_only fields for response.
            for name, schema in item_schema['properties'].copy().items():
                if 'writeOnly' in schema:
                    del item_schema['properties'][name]
                    if 'required' in item_schema:
                        item_schema['required'] = [f for f in item_schema['required'] if f != name]

        if is_list_view(path, method, self.view):
            response_schema = {
                'type': 'array',
                'items': item_schema,
            }
            paginator = self._get_paginator()
            if paginator:
                response_schema = paginator.get_paginated_response_schema(response_schema)
        else:
            response_schema = item_schema

        if (
            path not in self.response_codes.keys() or
            method not in self.response_codes[path].keys() or
            not self.response_codes[path][method]
        ):
            return {
                '200': {
                    'content': {
                        ct: {'schema': response_schema}
                        for ct in self.response_media_types
                    },
                    # description is a mandatory property,
                    # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#responseObject
                    # TODO: put something meaningful into it
                    'description': ""
                }
            }
        return {
            str(k): {'description': v.replace("[DEFAULT]", ""),
                **({'content': {
                        ct: {'schema': response_schema}
                        for ct in self.response_media_types
                    }} if "[DEFAULT]" in v else {})}
            for k, v in self.response_codes[path][method].items()
        }
