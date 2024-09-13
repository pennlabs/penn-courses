import inspect
import json
import re
from copy import deepcopy
from inspect import getdoc
from textwrap import dedent

import jsonref
from django.db import models
from django.urls import get_resolver
from rest_framework import serializers
from rest_framework.fields import _UnvalidatedField
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONOpenAPIRenderer
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.schemas.utils import is_list_view
from rest_framework.settings import api_settings


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


TERMINOLOGY:

Each route (e.g. GET /api/plan/schedules/{id}/) has an "operation ID" that is (by default)
automatically parsed from the codebase (e.g. "Retrieve Schedule"). The base "name" underlying this
operation ID is also automatically parsed by default (e.g. "Schedule"). The operation ID shows up
as the title of the route on our Redoc documentation page. You can customize the
name and/or the operation ID of a route by modifying the custom_name and custom_operation_id
dicts in this file. Customizing the name will change the operation ID and the tag of the route
(see below). You can customize the name with the custom_name dict below, and the operation ID
with the custom_operation_id dict.

Tags are groupings of routes by name. For instance, all the routes
GET, POST /api/plan/schedules/ and GET, PUT, DELETE /api/plan/schedules/{id}
are organized under the shared tag "[PCP] Schedule", since they all share the base name "Schedule".
You can click on a tag in the table of contents of our Redoc documenation, and the section will
expand to show all the underlying routes (each titled by its operation ID). You can change tag
names using the custom_tag_names dict below, but the default tag names are usually sensible
(derived from the base name of the underlying routes). What's more useful is to give a tag a
description, which you can do with the custom_tag_descriptions dict.

Tag groups organize tags into groups; they show up in the left sidebar of our Redoc page and divide
the categories of routes into meta categories. We are using them to separate our tags by app.
For instance, "Penn Course Plan" is a tag group. Each tag group has an abbreviation, specified by
the tag_group_abbreviations dict. For instance, the "Penn Course Plan" tag group is
abbreviated "[PCP]". Each tag in a tag group is prefixed by the tag group abbreviation in
square brackets (for instance "[PCP] Schedule"). The subpath_abbreviations dict below takes Django
app names (e.g. "plan"), and maps them to the corresponding tag group abbreviation (this is how
tags are automatically organized into tag groups). You shouldn't need to modify this dict unless
you change an app name or add a new app). Then, the tag_group_abbreviations dict maps the
abbreviation to the full name of the tag group.


MAINTENENCE:

You can update the introductory sections / readme of the auto-docs page by editing the
markdown-formatted openapi_description text below.
You should include docstrings in views (the proper format of docstrings are specified here
https://www.django-rest-framework.org/coreapi/from-documenting-your-api/#documenting-your-views)
explaining the function of the view (or the function of each method if there are multiple supported
methods). These docstrings will be parsed by the auto-docs and included in the documentation page.

When writing any class-based views where you specify a queryset (such as ViewSets), even if you
override get_queryset(), you should also specify the queryset field with something like
queryset = ExampleModel.objects.none() (using .none() to prevent accidental data breach), or
alternatively a sensible queryset default (e.g. queryset = Course.with_reviews.all() for the
CourseDetail ViewSet). Basically, just make sure the queryset parameter is always pointing to the
relevant model (if you are using queryset or get_queryset()). This will allow the
auto-documentation to access the model underlying the queryset (it cannot call get_queryset()
since it cannot generate a request object which the get_queryset() method might try to access).

If the meaning of a model or serializer field is not clear, you should include the string help_text
as a parameter when initializing the field, explaining what that field stores. This will show up
in the documentation such that parameter descriptions are inferred from model or serializer field
help text. For properties, the docstring will be used since there is no
way to define help_text for a property; so even if a property's use is clear based on the code,
keep in mind that describing its purpose in the docstring will be helpful to frontend engineers
who are unfamiliar with the backend code (also, don't include a :return: tag as you might normally
do for functions; a property is to be treated as a dynamic field, not a method, so just state
what the method returns as the only text in the docstring).
Including help_text/docstring when a field/property's purpose is unclear will also
make the model/serializer code more understandable for future Labs developers.
And furthermore, all help_text and descriptive docstrings show up in the backend
documentation (accessible at /admin/doc/).

PcxAutoSchema (defined below) is a subclass of Django's AutoSchema, and it makes some improvements
on that class for use with Redoc as well as some customizations specific to our use-cases. You can
customize auto-docs for a specific view by setting
schema = PcxAutoSchema(...)
in class-based views, or using the decorator
@schema(PcxAutoSchema(...))
in functional views, and passing kwargs (...) into the PcxAutoSchema constructor (search
PcxAutoSchema in our codebase for some examples of this, and keep reading for a comprehensive
description of how you can customize PcxAutoSchema using these kwargs).

There are a number of dictionaries you can use to customize these auto-docs; some are passed into
PcxAutoSchema as initialization kwargs, and some are predefined in this file (in the
"Customizable Settings" section below). Often, these dictionaries will contain layers of nested
dictionaries with a schema of path/method/... However, you will notice in example code snippets
in this README and in our codebase, these paths are not hardcoded but instead are referenced by
route name (to avoid repeating URL information that is already specified in urls.py files).
To determine the name of a certain URL, run `python manage.py show_urls` which will print
a list of URLs and their corresponding names.
Note that the route name of the URL here is not to be confused with the base name of the route
as defined above in the TERMINOLOGY section; the name of the URL is specified in the urls.py file,
whereas the name of the route is auto-generated from the code, and may or may not be derived from
the URL name. For instance "courses-detail" is a URL name, and "Course" is the base name of the
corresponding route for documentation generation.
Sorry for the confusion / overloading of terms here.

By default, response codes will be assumed to be 204 (for delete) or 200 (in all other cases).
To set custom response codes for a path/method (with a custom description), include a
response_codes kwarg in your PcxAutoSchema instantiation.  You should input
a dict mapping paths (indicated by route name) to dicts, where each subdict maps string methods
to dicts, and each further subdict maps int response codes to string descriptions.  An example:
    response_codes={
        "schedules-list": {
           "GET": {
               200: "[DESCRIBE_RESPONSE_SCHEMA]Schedules listed successfully.",
           },
           "POST": {
               201: "Schedule successfully created.",
               200: "Schedule successfully updated (a schedule with the "
                    "specified id already existed).",
               400: "Bad request (see description above).",
           }
        },
        ...
    }
Note that if you include "[DESCRIBE_RESPONSE_SCHEMA]" in your string description, that will
not show up in the description text (it will automatically be removed) but instead will indicate
that that response should have a response body schema show up in the documentation (the schema will
be automatically generated by default, but can be customized using the override_response_schema
kwarg; see below).  You should generally enable a response schema for responses which will contain
useful data for the frontend beyond the response code.  Note that in the example above, the only
such response is the listing of schedules (the GET 200 response).
If you include "[UNDOCUMENTED]" in your string description, that will
remove that response status code from the schema/docs. This is useful if you want to remove
a code that is included by default from the schema.

If you want to make manual changes to a request schema, include an override_request_schema kwarg
in your PcxAutoSchema instantiation.  You should input a dict mapping paths (indicated by
route name) to dicts, where each subdict maps string methods to objects specifying the
desired response schema for that path/method.
The format of these objects is governed by the OpenAPI specification
(for more on the syntax of how to specify a schema, see this link:
http://spec.openapis.org/oas/v3.0.3.html#schema-object [section 4.7.24]
you are specifying the dicts mapped to by "schema" keys in the examples at the following link:
http://spec.openapis.org/oas/v3.0.3.html#request-body-object).  An example:
    override_request_schema={
        "recommend-courses": {
            "POST": {
                "type": "object",
                "properties": {
                    "past_courses": {
                        "type": "array",
                        "description": (
                            "An array of courses the user has previously taken."
                        ),
                        "items": {
                            "type": "string",
                            "description": "A course code of the form DEPT-XXXX, e.g. CIS-120"
                        }
                    }
                }
            }
        }
    }

If you want to make manual changes to a response schema, include an override_response_schema kwarg
in your PcxAutoSchema instantiation.  You should input a dict mapping paths (indicated by
route name) to dicts, where each subdict maps string methods to dicts, and each further subdict
maps int response codes to the objects specifying the desired response schema.
The format of these objects is governed by the OpenAPI specification
(for more on the syntax of how to specify a schema, see this link:
http://spec.openapis.org/oas/v3.0.3.html#schema-object [section 4.7.24]
you are specifying the dicts mapped to by "schema" keys in the examples at the following link:
http://spec.openapis.org/oas/v3.0.3.html#response-object). You can reference existing schemas
generated by the docs using the notation {"$ref": "#/components/schemas/VeryComplexType"}.
Download the existing OpenAPI schema using the button at the top of the docs page to inspect
what existing schemas exist, and what the path to them is.

An example:
    override_response_schema={
        "recommend-courses": {
            "POST": {
                200: {
                    "type": "array",
                    "description": "An array of courses that we recommend.",
                    "items": {
                        "type": "string",
                        "description": "The full code of the recommended course, in the form "
                                       "DEPT-XXXX, e.g. CIS-1200"
                    }
                }
            }
        }
    }

You can also include a "media_type" key in the schema object of your custom response,
for setting a nonstandard response content type.

An example:
    override_response_schema={
        "calendar-view": {
            "GET": {
                200: {
                    "media_type": "text/calendar",
                    "type": "string",
                    "description": "A calendar file in ICS format."
                }
            }
        }
    }

If you want to manually set the description of a path parameter for a certain path/method,
you can do so by including a custom_path_parameter_desc kwarg in your PcxAutoSchema instantiation,
with keys of the form path > method > variable_name pointing to a string description.  Example:
    custom_path_parameter_desc={
        "statusupdate": {
            "GET": {
                "full_code": (
                    "The code of the section which this status update applies to, in the "
                    "form '{dept code}-{course code}-{section code}', e.g. 'CIS-120-001' for the "
                    "001 section of CIS-120."
                )
            }
        }
    }

If you want to manually specify parameters (query, path, header, or cookie) for a certain 
path/method, you can do so by including a custom_parameters kwarg in your PcxAutoSchema
instantiation, passing a dict of the form path > method > [list of query param schema objects]. 
This kwarg will override custom_path_parameter_desc if they conflict.
The format of these objects is described by 
https://spec.openapis.org/oas/v3.0.3.html#parameter-object [section 4.7.12]
Example:
    custom_parameters={
        "course-plots": {
            "GET": [
                {
                    "name": "course_code",
                    "in": "path",
                    "description": "The dash-joined department and code of the course you want plots for, e.g. `CIS-120` for CIS-120.",  # noqa E501
                    "schema": {"type": "string"},
                    "required": True,
                },
                {
                    "name": "instructor_ids",
                    "in": "query",
                    "description": "A comma-separated list of instructor IDs with which to filter the sections underlying the returned plots.",  # noqa E501
                    "schema": {"type": "string"},
                    "required": False,
                },
            ]
        },
    },

Finally, if you still need to further customize your API schema, you can do this in the
make_manual_schema_changes function below. This is applied to the final JSON schema after all
automatic changes / customizations are applied.  For more about the format of an OpenAPI
schema (which you would need to know a bit about to make further customizations), see this
documentation:
http://spec.openapis.org/oas/v3.0.3.html
To explore our JSON schema (which can help when trying to figure out how to modify it in
make_manual_schema_changes if you need to), you can download it from the /api/openapi/ route.
"""


def get_url_by_name(name):
    reverse = get_resolver().reverse_dict
    if name not in reverse:
        raise ValueError(f"Tried to get URL by name '{name}', but no such URL exists.")
    path = reverse[name][0][0][0]
    path = path.replace(r"%(pk)s", r"{id}")
    return "/" + re.sub(r"%\(([^)]+)\)s", r"{\1}", path)


# ============================= Begin Customizable Settings ========================================


# The following is the description which shows up at the top of the documentation site
openapi_description = """
# Introduction
Penn Courses ([GitHub](https://github.com/pennlabs/penn-courses)) is the umbrella
categorization for [Penn Labs](https://pennlabs.org/)
products designed to help students navigate the course registration process. It currently
includes three products, each with their own API documented on this page:
Penn Course Alert, Penn Course Plan, and Penn Course Review.

See `Penn Labs Notion > Penn Courses` for more details on each of our (currently) three apps.

For instructions on how to maintain this documentation while writing code,
see the comments in `backend/PennCourses/docs_settings.py` (it is easy, and will be helpful
for maintaining Labs knowledge in spite of our high member turnover rate).

See our [GitHub](https://github.com/pennlabs/penn-courses) repo for instructions on
installation, running in development, and loading in course data for development. Visit
the `/admin/doc/` route ([link](/admin/doc/)) for the backend documentation generated by Django
(admin account required, which can be made by running
`python manage.py createsuperuser` in terminal/CLI).

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

# Authentication
PCx user authentication is handled by platform's Penn Labs Accounts Engine.
See [Penn Labs Notion > Platform > The Accounts Engine](https://www.notion.so/pennlabs/The-Accounts-Engine-726ccf8875e244f4b8dbf8a8f2c97a87?pvs=4)
for extensive documentation and links to repositories for this system. When tags or routes
are described as requiring user authentication, they are referring to this system.

I highly recommend the [official video course on OAuth2](https://oauth.net/2/) (by Aaron Parecki),
then the Platform Notion docs on the "Accounts Engine" for anyone who wants to understand
Labs authentication better. Platform is our OAuth2 "Authorization Server",
and Django Labs Accounts is an OAuth2 client run by our Django backends (Clubs, Penn Courses, etc),
exposing client-facing authentication routes like `penncourseplan.com/accounts/login`.
There's also this Wikipedia page explaining [Shibboleth](https://en.wikipedia.org/wiki/Shibboleth_(software))
(which is used by Penn for authentication, and by the Platform authorization server).

See the Django docs for more on Django's features for
[User Authentication](https://docs.djangoproject.com/en/3.0/topics/auth/),
which are used by PCX apps, as part of Platform's accounts system.
"""  # noqa E501


# This dictionary takes app names (the string just after /api/ in the path or just after /
# if /api/ does not come at the beginning of the path)
# as values and abbreviated versions of those names as values.  It is used to
# add an abbreviated app prefix designating app membership to each route's tag name.
# For instance the Registration tag is prepended with [PCA] to get "[PCA] Registration" since
# its routes start with /api/alert/, and "alert": "PCA" is a key/value pair in the following dict.
subpath_abbreviations = {
    "plan": "PCP",
    "alert": "PCA",
    "review": "PCR",
    "base": "PCx",
    "accounts": "Accounts",
    "degree": "PDP",
}
assert all(
    [isinstance(key, str) and isinstance(val, str) for key, val in subpath_abbreviations.items()]
)


# This dictionary should map abbreviated app names (values from the dict above) to
# longer form names which will show up as the tag group name in the documentation.
tag_group_abbreviations = {
    "PCP": "Penn Course Plan",
    "PCA": "Penn Course Alert",
    "PCR": "Penn Course Review",
    "PCx": "Penn Courses (Base)",
    "Accounts": "Penn Labs Accounts",
    "": "Other"  # Catches all other tags (this should normally be an empty tag group and if so
    # it will not show up in the documentation, but is left as a debugging safeguard).
    # If routes are showing up in a "Misc" tag in this group, make sure you set the schema for
    # those views to be PcxAutoSchema, as is instructed in the meta docs above.
}
assert all(
    [isinstance(key, str) and isinstance(val, str) for key, val in tag_group_abbreviations.items()]
)


# "operation ids" are the unique titles of routes within a tag (if you click on a tag you see
# a list of operation ids, each corresponding to a certain route).

# name here refers to the name underlying the operation id of the view
# this is NOT the full name that you see on the API, it is the base name underlying it,
# and is used in construction of that name
# For instance, for POST /api/plan/schedules/, the name is "Schedule" and the operation_id is
# "Create Schedule" (see below get_name and _get_operation_id methods in PcxAutoSchema for
# a more in-depth explanation of the difference).
# IMPORTANT: The name also defines what the automatically-set tag name will be.
# That's why this custom_name is provided separately from custom_operation_id below;
# you can use it if you want to change the operation_id AND the tag name at once.
custom_name = {  # keys are (path, method) tuples, values are custom names
    # method is one of ("GET", "POST", "PUT", "PATCH", "DELETE")
    ("registrationhistory-list", "GET"): "Registration History",
    ("registrationhistory-detail", "GET"): "Registration History",
    ("statusupdate", "GET"): "Status Update",
    ("recommend-courses", "POST"): "Course Recommendations",
    ("course-reviews", "GET"): "Course Reviews",
    ("course-plots", "GET"): "Plots",
    ("review-autocomplete", "GET"): "Autocomplete Dump",
    ("instructor-reviews", "GET"): "Instructor Reviews",
    ("department-reviews", "GET"): "Department Reviews",
    ("course-history", "GET"): "Section-Specific Reviews",
    ("requirements-list", "GET"): "Pre-NGSS Requirement",
    ("restrictions-list", "GET"): "NGSS Restriction",
}
assert all(
    [isinstance(k, tuple) and len(k) == 2 and isinstance(k[1], str) for k in custom_name.keys()]
)


custom_operation_id = {  # keys are (path, method) tuples, values are custom names
    # method is one of ("GET", "POST", "PUT", "PATCH", "DELETE")
    ("registrationhistory-list", "GET"): "List Registration History",
    ("registrationhistory-detail", "GET"): "Retrieve Historic Registration",
    ("statusupdate", "GET"): "List Status Updates",
    ("courses-search", "GET"): "Course Search",
    ("section-search", "GET"): "Section Search",
    ("review-autocomplete", "GET"): "Retrieve Autocomplete Dump",
    ("calendar-view", "GET"): "Get Calendar",
}
assert all(
    [
        isinstance(k, tuple) and len(k) == 2 and isinstance(k[1], str)
        for k in custom_operation_id.keys()
    ]
)


# Use this dictionary to rename tags, if you wish to do so
# keys are old tag names (seen on docs), values are new tag names
custom_tag_names = {}
assert all([isinstance(key, str) and isinstance(val, str) for key, val in custom_tag_names.items()])


# Note that you can customize the tag for all routes from a certain view by passing in a
# list containing only that tag into the tags kwarg of PcxAutoSchema instantiation
# (inherited behavior from Django AutoSchema:
# https://www.django-rest-framework.org/api-guide/schemas/#autoschema)

# tag descriptions show up in the documentation body below the tag name
custom_tag_descriptions = {
    # keys are tag names (after any name changes from above dicts), vals are descriptions
    "[PCP] Schedule": dedent(
        """
        These routes allow interfacing with the user's PCP Schedules for the current semester,
        stored on the backend. Ever since we integrated Penn Labs Accounts into PCP so that users
        can store their schedules across devices and browsers, we have stored users' schedules on
        our backend (rather than local storage).
        """
    ),
    "[PCP] Pre-NGSS Requirements": dedent(
        """
        These routes expose the pre-NGSS (deprecated since 2022B) academic requirements for the
        current semester which are stored on our backend (hopefully comprehensive).
        """
    ),
    "[PCP] Course": dedent(
        """
        These routes expose course information for PCP for the current semester.
        """
    ),
    "[PCA] Registration History": dedent(
        """
        These routes expose a user's registration history (including
        inactive and obsolete registrations) for the current semester.  Inactive registrations are
        registrations which would not trigger a notification to be sent if their section opened,
        and obsolete registrations are registrations which are not at the head of their resubscribe
        chain.
        """
    ),
    "[PCA] Registration": dedent(
        """
        As the main API endpoints for PCA, these routes allow interaction with the user's
        PCA registrations.  An important concept which is referenced throughout the documentation
        for these routes is that of the "resubscribe chain".  A resubscribe chain is a chain
        of PCA registrations where the tail of the chain was an original registration created
        through a POST request to `/api/alert/registrations/` specifying a new section (one that
        the user wasn't already registered to receive alerts for).  Each next element in the chain
        is a registration created by resubscribing to the previous registration (once that
        registration had triggered an alert to be sent), either manually by the user or
        automatically if auto_resubscribe was set to true.  Then, it follows that the head of the
        resubscribe chain is the most relevant Registration for that user/section combo; if any
        of the registrations in the chain are active, it would be the head.  And if the head
        is active, none of the other registrations in the chain are active.

        Note that a registration will send an alert when the section it is watching opens, if and
        only if it hasn't sent one before, it isn't cancelled, and it isn't deleted.  If a
        registration would send an alert when the section it is watching opens, we call it
        "active".  See the Create Registration docs for an explanation of how to create a new
        registration, and the Update Registration docs for an explanation of how you can modify
        a registration after it is created.

        In addition to sending alerts for when a class opens up, we have also implemented
        an optionally user-enabled feature called "close notifications".
        If a registration has close_notification enabled, it will act normally when the watched
        section opens up for the first time (triggering an alert to be sent). However, once the
        watched section closes, it will send another alert (the email alert will be in the same
        chain as the original alert) to let the user know that the section has closed. Thus,
        if a user sees a PCA notification on their phone during a class for instance, they won't
        need to frantically open up their laptop and check PennInTouch to see if the class is still
        open just to find that it is already closed.  To avoid spam and wasted money, we DO NOT
        send any close notifications over text. So the user must have an email saved or use
        push notifications in order to be able to enable close notifications on a registration.
        Note that the close_notification setting carries over across resubscriptions, but can be
        disabled at any time using Update Registration.

        After the PCA backend refactor in 2019C/2020A, all PCA Registrations have a `user` field
        pointing to the user's Penn Labs Accounts User object.  In other words, we implemented a
        user/accounts system for PCA which required that
        people log in to use the website. Thus, the contact information used in PCA alerts
        is taken from the user's User Profile.  You can edit this contact information using
        Update User or Partial Update User.  If push_notifications is set to True, then
        a push notification will be sent when the user is alerted, but no text notifications will
        be sent (as that would be a redundant alert to the user's phone). Otherwise, an email
        or a text alert is sent if and only if contact information for that medium exists in
        the user's profile.
        """
    ),
    "[PCA] User": dedent(
        """
        These routes expose a user's saved settings (from their Penn Labs Accounts user object).
        For PCA, the profile object is of particular importance; it stores the email and
        phone of the user (with a null value for either indicating the user doesn't want to be
        notified using that medium).
        """
    ),
    "[PCA] Sections": dedent(
        """
        This route is used by PCA to get data about sections.
        """
    ),
    "[Accounts] User": dedent(
        """
        These routes allow interaction with the User object of a Penn Labs Accounts user.
        We do not document `/accounts/...` authentication routes here, as they are described
        by the [Authentication](#section/Authentication) section, and the
        [Penn Labs Account Engine](https://www.notion.so/pennlabs/The-Accounts-Engine-726ccf8875e244f4b8dbf8a8f2c97a87?pvs=4)
        Notion page.
        """  # noqa E501
    ),
    "Miscs": dedent(
        """
        <span style="color:red;">WARNING</span>: This tag should not be used, and its existence
        indicates you may have forgotten to set a view's schema to PcxAutoSchema for the views
        under this tag. See the meta documentation in backend/PennCourses/docs_settings.py of our
        codebase for instructions on how to properly set a view's schema to PcxAutoSchema.
        """
    ),
}
assert all(
    [isinstance(key, str) and isinstance(val, str) for key, val in custom_tag_descriptions.items()]
)


labs_logo_url = "https://i.imgur.com/tVsRNxJ.png"


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

    data["info"]["x-logo"] = {"url": labs_logo_url, "altText": "Labs Logo"}
    data["info"]["contact"] = {"email": "contact@pennlabs.org"}

    # Make application/json the only content type
    def delete_other_content_types_dfs(dictionary):
        if not isinstance(dictionary, dict):
            return None
        dictionary.pop("application/x-www-form-urlencoded", None)
        dictionary.pop("multipart/form-data", None)
        for value in dictionary.values():
            delete_other_content_types_dfs(value)

    delete_other_content_types_dfs(data)


# ============================== End Customizable Settings =========================================


def split_camel(w):
    return re.sub("([a-z0-9])([A-Z])", lambda x: x.groups()[0] + " " + x.groups()[1], w)


def pluralize_word(s):
    return s + "s"  # naive solution because this is how it is done in DRF


# Customization dicts populated by PcxAutoSchema __init__ method calls

# A cumulative version of the response_codes parameter to PcxAutoSchema:
cumulative_response_codes = dict()
# A cumulative version of the override_request_schema parameter to PcxAutoSchema:
cumulative_override_request_schema = dict()
# A cumulative version of the override_response_schema parameter to PcxAutoSchema:
cumulative_override_response_schema = dict()
# A cumulative version of the custom_path_parameter_desc parameter to PcxAutoSchema:
cumulative_cppd = dict()
# A cumulative version of the custom_parameters parameter to PcxAutoSchema:
cumulative_cp = dict()


class JSONOpenAPICustomTagGroupsRenderer(JSONOpenAPIRenderer):
    def render(self, data_raw, media_type=None, renderer_context=None):
        """
        This overridden method modifies the JSON OpenAPI schema generated by Django
        to add tag groups, and most of the other customization specified above.
        It was written by referencing the existing schema at /api/openapi
        and also an example schema (written in YAML instead of JSON, but still
        easily interpretable as JSON) from a Redoc example:
        https://github.com/Redocly/redoc/blob/master/demo/openapi.yaml
        """

        # The following resolves JSON refs which are not handled automatically in Python dicts
        # https://swagger.io/docs/specification/using-ref/
        data = jsonref.loads(json.dumps(data_raw))

        # Determine existing tags and create a map from tag to a list of the corresponding dicts
        # of nested schema objects at paths/{path}/{method} in the OpenAPI schema (for all
        # the paths/methods which have that tag).
        # If any routes do not have tags, add the 'Misc' tag to them, which will be put in
        # the 'Other' tag group automatically, below.
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
                else:
                    v["tags"] = ["Misc"]
                    tags.add("Misc")
                    if "Misc" not in tag_to_dicts.keys():
                        tag_to_dicts["Misc"] = []
                    tag_to_dicts["Misc"].append(v)

        # A function to change tag names (adds requested changes to a dict which will be
        # cleared after the for tag in tags loop below finishes; it is done this way since
        # the tags set cannot be modified while it is being iterated over).
        changes = dict()

        def update_tag(old_tag, new_tag):
            for val in tag_to_dicts[old_tag]:
                val["tags"] = [(t if t != old_tag else new_tag) for t in val["tags"]]
            lst = tag_to_dicts.pop(old_tag)
            tag_to_dicts[new_tag] = lst
            changes[old_tag] = new_tag  # since tags cannot be updated while iterating through tags
            return new_tag

        # Pluralize tag name if all views in tag are lists, and apply custom tag names from
        # custom_tag_names dict defined above.
        for tag in tags:
            tag = update_tag(tag, split_camel(tag))
            all_list = all([("list" in v["operationId"].lower()) for v in tag_to_dicts[tag]])
            if all_list:  # if all views in tag are lists, pluralize tag name
                tag = update_tag(
                    tag, " ".join(tag.split(" ")[:-1] + [pluralize_word(tag.split(" ")[-1])])
                )
            if tag in custom_tag_names.keys():  # rename custom tags
                tag = update_tag(tag, custom_tag_names[tag])

        # Remove 'required' flags from responses (it doesn't make sense for a response
        # item to be 'required').
        def delete_required_dfs(dictionary):
            if not isinstance(dictionary, dict):
                return None
            dictionary.pop("required", None)
            for value in dictionary.values():
                delete_required_dfs(value)

        for path_name, val in data["paths"].items():
            for method_name, v in val.items():
                v["responses"] = deepcopy(v["responses"])
                delete_required_dfs(v["responses"])

        # Since tags could not be updated while we were iterating through tags above,
        # we update them now.
        for k, v in changes.items():
            tags.remove(k)
            tags.add(v)

        # Add custom tag descriptions from the custom_tag_descriptions dict defined above
        data["tags"] = [
            {"name": tag, "description": custom_tag_descriptions.get(tag, "")} for tag in tags
        ]

        # Add tags to tag groups based on the tag group abbreviation in the name of the tag
        # (these abbreviations are added as prefixes of the tag names automatically in the
        # get_tags method of PcxAutoSchema).
        tags_to_tag_groups = dict()
        for t in tags:
            for k in tag_group_abbreviations.keys():
                # Assigning the tag groups like this prevents tag abbreviations being substrings
                # of each other from being problematic; the longest matching abbreviation is
                # used (so even if another tag group abbreviation is a substring, it won't be
                # mistakenly used for the tag group).
                if k in t and (
                    t not in tags_to_tag_groups.keys() or len(k) > len(tags_to_tag_groups[t])
                ):
                    tags_to_tag_groups[t] = k
        data["x-tagGroups"] = [
            {"name": v, "tags": [t for t in tags if tags_to_tag_groups[t] == k]}
            for k, v in tag_group_abbreviations.items()
        ]
        # Remove empty tag groups
        data["x-tagGroups"] = [g for g in data["x-tagGroups"] if len(g["tags"]) != 0]

        # This code ensures that no path/methods in optional dictionary kwargs passed to
        # PcxAutoSchema __init__ methods are invalid (indicating user error)
        for original_kwarg, parameter_name, parameter_dict in [
            ("response_codes", "cumulative_response_codes", cumulative_response_codes),
            (
                "override_request_schema",
                "cumulative_override_request_schema",
                cumulative_override_request_schema,
            ),
            (
                "override_response_schema",
                "cumulative_override_response_schema",
                cumulative_override_response_schema,
            ),
            ("custom_path_parameter_desc", "cumulative_cppd", cumulative_cppd),
            ("custom_parameters", "cumulative_cp", cumulative_cp),
        ]:
            for route_name in parameter_dict:
                traceback = parameter_dict[route_name]["traceback"]
                path = get_url_by_name(route_name)
                if path not in data["paths"].keys():
                    raise ValueError(
                        f"Check the {original_kwarg} input to PcxAutoSchema instantiation at "
                        f"{traceback}; invalid path found: '{path}'."
                        + (
                            "If 'id' is in your args list, check if you set primary_key=True for "
                            "some field in the relevant model, and if so change 'id' "
                            "in your args list to the name of that field."
                            if "id" in path
                            else ""
                        )
                    )
                for method in parameter_dict[route_name]:
                    if method == "traceback":
                        continue
                    if method.lower() not in data["paths"][path].keys():
                        raise ValueError(
                            f"Check the {original_kwarg} input to PcxAutoSchema instantiation at "
                            f"{traceback}; invalid method '{method}' for path '{path}'"
                        )

        new_cumulative_cp = {
            get_url_by_name(route_name): value for route_name, value in cumulative_cp.items()
        }

        # Update query parameter documentation
        for path_name, val in data["paths"].items():
            if path_name not in new_cumulative_cp:
                continue
            for method_name, v in val.items():
                method_name = method_name.upper()
                if method_name.upper() not in new_cumulative_cp[path_name]:
                    continue
                custom_query_params = new_cumulative_cp[path_name][method_name]
                custom_query_params_names = {param_ob["name"] for param_ob in custom_query_params}
                v["parameters"] = [
                    param_ob
                    for param_ob in v["parameters"]
                    if param_ob["name"] not in custom_query_params_names
                ] + custom_query_params

        # Make any additional manual changes to the schema programmed by the user
        make_manual_schema_changes(data)

        return jsonref.dumps(data, indent=2).encode("utf-8")


class PcxAutoSchema(AutoSchema):
    """
    This custom subclass serves to improve AutoSchema in terms of customizability, and
    quality of inference in some non-customized cases.

    https://www.django-rest-framework.org/api-guide/schemas/#autoschema
    """

    def __new__(
        cls,
        *args,
        response_codes=None,
        override_request_schema=None,
        override_response_schema=None,
        custom_path_parameter_desc=None,
        custom_parameters=None,
        **kwargs,
    ):
        """
        An overridden __new__ method which adds a created_at property to each PcxAutoSchema
        instance indicating the file/line from which it was instantiated (useful for debugging).
        """
        new_instance = super(PcxAutoSchema, cls).__new__(cls, *args, **kwargs)
        stack_trace = inspect.stack()
        created_at = "%s:%d" % (stack_trace[1][1], stack_trace[1][2])
        new_instance.created_at = created_at
        return new_instance

    # Overrides, uses overridden method
    # https://www.django-rest-framework.org/api-guide/schemas/#autoschema__init__-kwargs
    def __init__(
        self,
        *args,
        response_codes=None,
        override_request_schema=None,
        override_response_schema=None,
        custom_path_parameter_desc=None,
        custom_parameters=None,
        **kwargs,
    ):
        """
        This custom __init__ method deals with optional passed-in kwargs such as
        response_codes, override_response_schema, and custom_path_parameter_desc.
        """

        def fail(param, hint):
            """
            A function to generate an error message if validation of one of the passed-in
            kwargs fails.
            """
            raise ValueError(
                f"Invalid {param} kwarg passed into PcxAutoSchema at {self.created_at}; please "
                f"check the meta docs in PennCourses/docs_settings.py for an explanation of "
                f"the proper format of this kwarg. Hint:\n{hint}"
            )

        # Validate that each of the passed-in kwargs are nested dictionaries of the correct depth
        for param_name, param_dict in [
            ("response_codes", response_codes),
            ("override_request_schema", override_request_schema),
            ("override_response_schema", override_response_schema),
            ("custom_path_parameter_desc", custom_path_parameter_desc),
            ("custom_parameters", custom_parameters),
        ]:
            if param_dict is not None:
                if not isinstance(param_dict, dict):
                    fail(param_name, f"The {param_name} kwarg must be a dict.")
                for dictionary in param_dict.values():
                    if not isinstance(dictionary, dict):
                        fail(param_name, f"All values of the {param_name} dict must be dicts.")
                    for nested_dictionary in dictionary.values():
                        if param_name == "custom_parameters":
                            if not isinstance(nested_dictionary, list):
                                fail(
                                    param_name,
                                    f"All values of the dict values of {param_name} must be lists.",
                                )
                            continue
                        if not isinstance(nested_dictionary, dict):
                            fail(
                                param_name,
                                f"All values of the dict values of {param_name} must be dicts.",
                            )
                        if param_name in [
                            "override_request_schema",
                            "override_response_schema",
                        ]:
                            continue
                        for value in nested_dictionary.values():
                            if isinstance(value, dict):
                                fail(
                                    param_name,
                                    f"Too deep nested dictionaries found in {param_name}.",
                                )

        # Handle passed-in custom response codes
        global cumulative_response_codes
        if response_codes is None:
            self.response_codes = dict()
        else:
            response_codes = deepcopy(response_codes)
            for key, d in response_codes.items():
                response_codes[key] = {k.upper(): v for k, v in d.items()}
            self.response_codes = response_codes
            for_cumulative_response_codes = deepcopy(response_codes)
            for dictionary in for_cumulative_response_codes.values():
                dictionary["traceback"] = self.created_at
            cumulative_response_codes = {
                **cumulative_response_codes,
                **for_cumulative_response_codes,
            }

        # Handle passed-in customized request schemas
        global cumulative_override_request_schema
        if override_request_schema is None:
            self.override_request_schema = dict()
        else:
            override_request_schema = deepcopy(override_request_schema)
            for key, d in override_request_schema.items():
                override_request_schema[key] = {k.upper(): v for k, v in d.items()}
            self.override_request_schema = override_request_schema
            for_cumulative_override_request_schema = deepcopy(override_request_schema)
            for dictionary in for_cumulative_override_request_schema.values():
                dictionary["traceback"] = self.created_at
            cumulative_override_request_schema = {
                **cumulative_override_request_schema,
                **for_cumulative_override_request_schema,
            }

        # Handle passed-in customized response schemas
        global cumulative_override_response_schema
        if override_response_schema is None:
            self.override_response_schema = dict()
        else:
            override_response_schema = deepcopy(override_response_schema)
            for key, d in override_response_schema.items():
                override_response_schema[key] = {k.upper(): v for k, v in d.items()}
            self.override_response_schema = override_response_schema
            for_cumulative_override_response_schema = deepcopy(override_response_schema)
            for dictionary in for_cumulative_override_response_schema.values():
                dictionary["traceback"] = self.created_at
            cumulative_override_response_schema = {
                **cumulative_override_response_schema,
                **for_cumulative_override_response_schema,
            }

        # Handle passed-in custom path parameter descriptions
        global cumulative_cppd
        if custom_path_parameter_desc is None:
            self.custom_path_parameter_desc = dict()
        else:
            custom_path_parameter_desc = deepcopy(custom_path_parameter_desc)
            for key, d in custom_path_parameter_desc.items():
                custom_path_parameter_desc[key] = {k.upper(): v for k, v in d.items()}
            self.custom_path_parameter_desc = custom_path_parameter_desc
            for_cumulative_cppd = deepcopy(custom_path_parameter_desc)
            for dictionary in for_cumulative_cppd.values():
                dictionary["traceback"] = self.created_at
            cumulative_cppd = {**cumulative_cppd, **for_cumulative_cppd}

        # Handle passed-in custom query parameter descriptions
        global cumulative_cp
        if custom_parameters is not None:
            custom_parameters = deepcopy(custom_parameters)
            for key, d in custom_parameters.items():
                custom_parameters[key] = {k.upper(): v for k, v in d.items()}
            for dictionary in custom_parameters.values():
                dictionary["traceback"] = self.created_at
            cumulative_cp = {**cumulative_cp, **custom_parameters}

        super().__init__(*args, **kwargs)

    # Overrides, uses overridden method
    def get_description(self, path, method):
        """
        This overridden method adds the method and path to the top of each route description
        and a note if authentication is required (in addition to calling/using the
        super method). Docstring of overridden method:

        Determine a path description.

        This will be based on the method docstring if one exists,
        or else the class docstring.
        """

        # Add the method and path to the description so it is more readable.
        desc = f"({method.upper()} `{path}`)\n\n"
        # Add the description from docstrings (default functionality).
        desc += super().get_description(path, method)
        view = self.view
        # Add a note if the path/method requires user authentication.
        if IsAuthenticated in view.permission_classes:
            desc += '\n\n<span style="color:red;">User authentication required</span>.'
        return desc

    # Overrides, uses overridden method
    # (https://www.django-rest-framework.org/api-guide/schemas/#map_serializer)
    def map_serializer(self, serializer):
        """
        This method adds property docstrings as field descriptions when appropriate
        (to request/response schemas in the API docs), in addition
        to calling the overridden map_serializer function.
        For instance, in the response schema of
        [PCA] Registration, List Registration (GET /api/alert/registrations/)
        the description of the is_active property is inferred from the property docstring
        by this method (before it was blank).
        """

        result = super().map_serializer(serializer)

        properties = result["properties"]
        model = None
        if hasattr(serializer, "Meta") and hasattr(serializer.Meta, "model"):
            model = serializer.Meta.model

        for field in serializer.fields.values():
            if isinstance(field, serializers.HiddenField):
                continue
            schema = properties[field.field_name]
            if (
                "description" not in schema
                and model is not None
                and hasattr(model, field.field_name)
                and isinstance(getattr(model, field.field_name), property)
                and getattr(model, field.field_name).__doc__
            ):
                schema["description"] = dedent(getattr(model, field.field_name).__doc__)

        return result

    # Overrides, uses overridden method
    # (https://www.django-rest-framework.org/api-guide/schemas/#map_field)
    def map_field(self, field):

        # Nested Serializers, `many` or not.
        if isinstance(field, serializers.ListSerializer):
            return {"type": "array", "items": []}
        if isinstance(field, serializers.Serializer):
            data = self.map_serializer(field)
            data["type"] = "object"
            return data

        # Related fields.
        if isinstance(field, serializers.ManyRelatedField):
            return {"type": "array", "items": self.map_field(field.child_relation)}
        if isinstance(field, serializers.PrimaryKeyRelatedField):
            if getattr(field, "pk_field", False):
                return self.map_field(field=field.pk_field)
            model = getattr(field.queryset, "model", None)
            if model is not None:
                model_field = model._meta.pk
                if isinstance(model_field, models.AutoField):
                    return {"type": "integer"}

        # ChoiceFields (single and multiple).
        # Q:
        # - Is 'type' required?
        # - can we determine the TYPE of a choicefield?
        if isinstance(field, serializers.MultipleChoiceField):
            return {"type": "array", "items": self.map_choicefield(field)}

        if isinstance(field, serializers.ChoiceField):
            return self.map_choicefield(field)

        # ListField.
        if isinstance(field, serializers.ListField):
            mapping = {
                "type": "array",
                "items": {},
            }
            if not isinstance(field.child, _UnvalidatedField):
                mapping["items"] = self.map_field(field.child)
            return mapping

        # DateField and DateTimeField type is string
        if isinstance(field, serializers.DateField):
            return {
                "type": "string",
                "format": "date",
            }

        if isinstance(field, serializers.DateTimeField):
            return {
                "type": "string",
                "format": "date-time",
            }

        # "Formats such as "email", "uuid", and so on, MAY be used even though undefined by this
        # specification."
        # see: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#data-types
        # see also: https://swagger.io/docs/specification/data-models/data-types/#string
        if isinstance(field, serializers.EmailField):
            return {"type": "string", "format": "email"}

        if isinstance(field, serializers.URLField):
            return {"type": "string", "format": "uri"}

        if isinstance(field, serializers.UUIDField):
            return {"type": "string", "format": "uuid"}

        if isinstance(field, serializers.IPAddressField):
            content = {
                "type": "string",
            }
            if field.protocol != "both":
                content["format"] = field.protocol
            return content

        if isinstance(field, serializers.DecimalField):
            if getattr(field, "coerce_to_string", api_settings.COERCE_DECIMAL_TO_STRING):
                content = {
                    "type": "string",
                    "format": "decimal",
                }
            else:
                content = {"type": "number"}

            if field.decimal_places:
                content["multipleOf"] = float("." + (field.decimal_places - 1) * "0" + "1")
            if field.max_whole_digits:
                content["maximum"] = int(field.max_whole_digits * "9") + 1
                content["minimum"] = -content["maximum"]
            self._map_min_max(field, content)
            return content

        if isinstance(field, serializers.FloatField):
            content = {
                "type": "number",
            }
            self._map_min_max(field, content)
            return content

        if isinstance(field, serializers.IntegerField):
            content = {"type": "integer"}
            self._map_min_max(field, content)
            # 2147483647 is max for int32_size, so we use int64 for format
            if int(content.get("maximum", 0)) > 2147483647:
                content["format"] = "int64"
            if int(content.get("minimum", 0)) > 2147483647:
                content["format"] = "int64"
            return content

        if isinstance(field, serializers.FileField):
            return {"type": "string", "format": "binary"}

        # Simplest cases, default to 'string' type:
        FIELD_CLASS_SCHEMA_TYPE = {
            serializers.BooleanField: "boolean",
            serializers.JSONField: "object",
            serializers.DictField: "object",
            serializers.HStoreField: "object",
        }
        return {"type": FIELD_CLASS_SCHEMA_TYPE.get(field.__class__, "string")}

    # Helper method
    def get_action(self, path, method):
        """
        This method gets the action of the specified path/method (a more expressive name
        for the method like "retrieve" or "list" for a GET method or "create" for a POST method).
        The code is taken from the get_operation_id_base method in AutoSchema,
        but is slightly modified to not use camelCase.
        """
        method_name = getattr(self.view, "action", method.lower())
        if is_list_view(path, method, self.view):
            action = "list"
        elif method_name not in self.method_mapping:
            action = method_name.lower()
        else:
            action = self.method_mapping[method.lower()]
        return action

    # Helper method
    def get_name(self, path, method, action=None):
        """
        This method returns the name of the path/method. If the
        user has specified a custom name using the custom_name parameter to __init__, that custom
        name is used.
        The code here is backported/modified from AutoSchema's get_operation_id_base method
        due to how we generate tags (when "s" is added to the end of names for list actions in
        get_operation_id_base, this makes it impossible to tag those list action routes together
        with their non-list counterparts using their shared names as we like to do).
        Besides not appending "s", this backported code is also modified to remove
        the "viewset" suffix from the name if it exists.
        All modified code is marked by a comment starting with "MODIFIED"
        I am probably going to submit a PR to DRF to try to get them to improve their
        default tag generation in this way (eventually).
        If that ever gets merged and cut into a stable release, we will be able to
        remove this method from our code.
        Otherwise, keep an eye on DRF changes to see if the overridden get_operation_id_base
        method is improved (and incorperate those changes here if possible).
        """

        # Return the custom name if specified by the user
        # First convert the functions in the tuple keys of custom_name to strings
        custom_name_converted_keys = {
            (get_url_by_name(route_name), m): v for (route_name, m), v in custom_name.items()
        }
        # Check if user has specified custom name
        if (path, method) in custom_name_converted_keys.keys():
            return custom_name_converted_keys[(path, method)]

        # Get action if it is not passed in as a parameter
        if action is None:
            action = self.get_action(path, method)

        # NOTE: All below code is taken/modified from AutoSchema's get_operation_id_base method

        model = getattr(getattr(self.view, "queryset", None), "model", None)

        if self.operation_id_base is not None:
            name = self.operation_id_base

        # Try to deduce the ID from the view's model
        elif model is not None:
            name = model.__name__

        # Try with the serializer class name
        elif self.get_serializer(path, method) is not None:
            name = self.get_serializer(path, method).__class__.__name__
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
                # MODIFIED from AutoSchema's get_operation_id_base: remove viewset suffix
                name = name[:-7]

            # Due to camel-casing of classes and `action` being lowercase, apply title in order to
            # find if action truly comes at the end of the name
            if name.endswith(action.title()):  # ListView, UpdateAPIView, ThingDelete ...
                name = name[: -len(action)]

        # MODIFIED from AutoSchema's get_operation_id_base: "s" is not appended
        # even if action is list

        return name

    # Overrides, DOES NOT call overridden method
    # https://www.django-rest-framework.org/api-guide/schemas/#get_operation_id_base
    def get_operation_id_base(self, path, method, action):
        """
        This method returns the base operation id (i.e. the name) of the path/method. It
        uses get_name as a helper but makes the last character "s" if the action is "list".
        See the docstring for the get_name method of this class for an explanation as
        to why we do this. Docstring of overridden method:

        Compute the base part for operation ID from the model, serializer or view name.
        """

        name = self.get_name(path, method, action)

        if action == "list" and not name.endswith("s"):  # listThings instead of listThing
            name = pluralize_word(name)

        return name

    # Overrides, uses overridden method
    # https://www.django-rest-framework.org/api-guide/schemas/#get_operation_id
    def get_operation_id(self, path, method):
        """
        This method gets the operation id for the given path/method. It first checks if
        the user has specified a custom operation id for this path/method using the
        custom_operation_id dict at the top of docs_settings.py, and if not it returns the result
        of the overridden method (which is modified from default by the overriden
        get_operation_id_base method above). Docstring of overridden method:

        Compute an operation ID from the view type and get_operation_id_base method.
        """

        # Return the custom operation id if specified by the user
        # First convert the functions in the tuple keys of custom_operation_id to strings
        custom_operation_id_converted_keys = {
            (get_url_by_name(route_name), m): v
            for (route_name, m), v in custom_operation_id.items()
        }
        # Check if user has specified custom operation id
        if (path, method) in custom_operation_id_converted_keys.keys():
            return custom_operation_id_converted_keys[(path, method)]

        return split_camel(super().get_operation_id(path, method)).title()

    # Overrides, DOES NOT call overridden method
    # Keep an eye on DRF changes to see if the overridden get_tags method is improved
    # https://www.django-rest-framework.org/api-guide/schemas/#get_tags
    def get_tags(self, path, method):
        """
        This method returns custom tags passed into the __init__ method, or otherwise
        (if the tags argument was not included) adds a tag
        of the form '[APP] route_name' as the default behavior.
        Note that the abbreviation of the app in these [APP] brackets is set in the
        subpath_abbreviations dict above.
        """

        # If user has specified tags, use them.
        if self._tags:
            return self._tags

        # Create the tag from the first part of the path (other than "api") and the name
        name = self.get_name(path, method)
        path_components = (path[1:] if path.startswith("/") else path).split("/")
        subpath = path_components[1] if path_components[0] == "api" else path_components[0]
        if subpath not in subpath_abbreviations.keys():
            raise ValueError(
                f"You must add the the '{subpath}' subpath to the "
                "subpath_abbreviations dict in backend/PennCourses/docs_settings.py. "
                f"This subpath was inferred from the path '{path}'."
            )
        return [f"[{subpath_abbreviations[subpath]}] {name}"]

    # Overrides, uses overridden method
    def get_path_parameters(self, path, method):
        """
        This method returns a list of parameters from templated path variables. It improves
        the inference of path parameter description from the overridden method by utilizing
        property docstrings. If a custom path parameter description is specified using the
        custom_path_parameter_desc kwarg in __init__, that is used for the description.
        Docstring of overridden method:

        Return a list of parameters from templated path variables.
        """

        parameters = super().get_path_parameters(path, method)

        model = getattr(getattr(self.view, "queryset", None), "model", None)
        for parameter in parameters:
            variable = parameter["name"]
            description = parameter["description"]

            # Use property docstrings when possible
            if model is not None:
                try:
                    model_field = model._meta.get_field(variable)
                except Exception:
                    model_field = None
                if (
                    model_field is None
                    and parameter["name"] in model.__dict__.keys()
                    and isinstance(model.__dict__[variable], property)
                ):
                    doc = getdoc(model.__dict__[variable])
                    description = "" if doc is None else doc

            custom_path_parameter_desc = {
                get_url_by_name(route_name): value
                for route_name, value in self.custom_path_parameter_desc.items()
            }

            # Add custom path parameter description if relevant
            if (
                custom_path_parameter_desc
                and path in custom_path_parameter_desc.keys()
                and method.upper() in custom_path_parameter_desc[path].keys()
                and variable in custom_path_parameter_desc[path][method].keys()
                and custom_path_parameter_desc[path][method][variable]
            ):
                description = custom_path_parameter_desc[path][method][variable]

            parameter["description"] = description

        return parameters

    # Overrides, uses overridden method
    def get_request_body(self, path, method):
        """
        This method overrides the get_request_body method from AutoSchema, setting
        a custom request schema if specified via the override_request_schema init kwarg.
        """
        request_body = super().get_request_body(path, method)

        override_request_schema = {
            get_url_by_name(route_name): value
            for route_name, value in self.override_request_schema.items()
        }

        if path in override_request_schema and method in override_request_schema[path]:
            for ct in request_body["content"]:
                request_body["content"][ct]["schema"] = override_request_schema[path][method]

        return request_body

    # Overrides, uses overridden method
    def get_responses(self, path, method):
        """
        This method describes the responses for this path/method. It makes certain
        improvements over the overridden method in terms of adding useful information
        (like 403 responses). It also enforces the user's choice as to whether to include
        a response schema or alternatively just display the response (for path/method/status_code).
        Custom response descriptions specified by the user in the response_codes
        kwarg to the __init__ method are also added.
        Finally, custom schemas specified by the user in the override_response_schema kwarg to the
        __init__ method are added.
        """

        responses = super().get_responses(path, method)

        # Automatically add 403 response if authentication is required
        if IsAuthenticated in self.view.permission_classes and 403 not in responses:
            responses = {
                **responses,
                403: {"description": "Access denied (missing or improper authentication)."},
            }

        # Get "default" schema content from response
        # This code is from an older version of the overridden method which
        # did not use JSON refs (JSON refs are not appropriate for our use-case since
        # we change certain response schemas in ways that we don't want to affect
        # request schemas, etc).
        serializer = self.get_response_serializer(path, method)
        if not isinstance(serializer, serializers.Serializer):
            item_schema = {}
        else:
            item_schema = self.get_reference(serializer)
        if is_list_view(path, method, self.view):
            response_schema = {
                "type": "array",
                "items": item_schema,
            }
            paginator = self.get_paginator()
            if paginator:
                response_schema = paginator.get_paginated_response_schema(response_schema)
        else:
            response_schema = item_schema
        default_schema_content = {
            content_type: {"schema": deepcopy(response_schema)}
            for content_type in self.response_media_types
        }

        response_codes = {
            get_url_by_name(route_name): value for route_name, value in self.response_codes.items()
        }

        # Change all status codes to integers
        responses = {int(key): value for key, value in responses.items()}
        # Add status codes and custom descriptions from custom response_codes dict
        if path in response_codes and method in response_codes[path]:
            for status_code in response_codes[path][method]:
                status_code = int(status_code)
                custom_description = response_codes[path][method][status_code]
                include_content = "[DESCRIBE_RESPONSE_SCHEMA]" in custom_description
                custom_description = custom_description.replace("[DESCRIBE_RESPONSE_SCHEMA]", "")
                if status_code in responses.keys():
                    if "[UNDOCUMENTED]" in custom_description:
                        del responses[status_code]
                    else:
                        responses[status_code]["description"] = custom_description
                        if not include_content and "content" in responses[status_code]:
                            del responses[status_code]["content"]
                elif "[UNDOCUMENTED]" not in custom_description:
                    responses[status_code] = {"description": custom_description}
                    if include_content:
                        responses[status_code]["content"] = deepcopy(default_schema_content)

        override_response_schema = {
            get_url_by_name(route_name): value
            for route_name, value in self.override_response_schema.items()
        }

        if path in override_response_schema and method in override_response_schema[path]:
            for status_code in override_response_schema[path][method]:
                if status_code not in responses.keys():
                    responses[status_code] = {
                        "description": "",
                        "content": deepcopy(default_schema_content),  # to be mutated below
                    }
            for status_code in responses.keys():
                if status_code in override_response_schema[path][method]:
                    custom_schema = override_response_schema[path][method][status_code]
                    custom_media_type = custom_schema.get("media_type")
                    if custom_media_type:
                        del custom_schema["media_type"]
                    if "content" not in responses[status_code]:
                        responses[status_code]["content"] = dict()
                        for ct in self.request_media_types:
                            responses[status_code]["content"][ct] = dict()
                            responses[status_code]["content"][ct]["schema"] = custom_schema
                    else:
                        for response_schema in responses[status_code]["content"].values():
                            response_schema["schema"] = custom_schema
                    if custom_media_type:
                        if custom_media_type not in responses[status_code]["content"]:
                            responses[status_code]["content"][custom_media_type] = dict()
                        responses[status_code]["content"][custom_media_type][
                            "schema"
                        ] = custom_schema
        return responses
