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
from rest_framework.permissions import IsAuthenticated


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
Or, if you are using function-based views, include the following decorator above your views:
@schema(PcxAutoSchema())
and include the following import in your views.py file:
from rest_framework.decorators import schema
(This is instructed in the DRF docs:
https://www.django-rest-framework.org/api-guide/views/#view-schema-decorator.)
In all cases, you must include the following import for PcxAutoSchema:
from PennCourses.docs_settings import PcxAutoSchema
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

By default, response codes will be assumed to be 204 (for delete) or 200 (in all other cases).
To set custom response codes for a path/method (with a custom description), include a 
response_codes kwarg in your PcxAutoSchema instantiation.  You should input 
a dict mapping string paths to dicts, where each subdict maps string methods to dicts, and 
each further subdict maps int response codes to string descriptions.  An example:
    response_codes={
        "/api/plan/schedules/": {
           "GET": {
               200: "[SCHEMA]Schedules listed successfully.",
               403: "Authentication credentials were not provided."
           },
           "POST": {
               201: "Schedule successfully created.",
               200: "Schedule successfully updated (a schedule with the "
                    "specified id already existed).",
               400: "Bad request (see description above).",
               403: "Authentication credentials were not provided."
           }
        },
        ...
    }
Note that if you include "[SCHEMA]" in your string description, that will not show up in the 
description text (it will automatically be removed) but instead will indicate that that response 
should have a response body schema show up in the documentation (the schema will be automatically 
generated by default, but can be customized using the override_schema kwarg; see below).  You 
should generally enable a response schema for responses which will contain useful data for the 
frontend beyond the response code.  Note that in the example above, the only such response is the 
listing of schedules (the GET 200 response).

You should add examples for an API routes if the auto-generated examples are not to 
your liking (they are usually not as good as actual examples with realistic values). 
You can do this by including an examples kwarg in your PcxAutoSchema instantiation.  You should input 
a dict mapping string paths to dicts, where each subdict maps string methods to dicts, and 
each further subdict is of the following form:
    {
        "requests": [...],
        "responses": [...]
    }
where requests and responses map to lists of dicts.  The dicts in these lists are examples objects, 
the format of which is governed by the OpenAPI specification 
(http://spec.openapis.org/oas/v3.0.3.html#fixed-fields-15) WITH ONE IMPORTANT ADDITION: 
you must include a "code":int key/value in any object in the responses list, specifying which response 
code that example corresponds to.  Here is a full example of the entire examples dict:
    examples = {
        "/api/alert/registrations/": {
            "POST": {
                "requests": [
                    {
                        "summary": "Maximally Customized POST",
                        "value": {
                            "section": "CIS-120-001",
                            "auto_resubscribe": True
                        }
                    }
                ],
                "responses": [
                    {
                        "code": 201,
                        "summary": "Registration Created Successfully",
                        "value": {
                            "message": "Your registration for CIS-120-001 was successful!",
                            "id": 1
                        }
                    }
                ]
            }
        }
        ...
    }
Since these examples can get quite long, it is good practice to move your examples dict to 
a separate examples.py file (and import the dict into your views.py file or wherever you are 
instantiating the PcxAutoSchema class).

If you want to make manual changes to a response schema, include an override_schema kwarg in your 
PcxAutoSchema instantiation.  You should input 
a dict mapping string paths to dicts, where each subdict maps string methods to dicts, and 
each further subdict maps int response codes to the objects specifying the desired response schema. 
The format of these objects is governed by the OpenAPI specification 
(see the dicts mapped to by "schema" keys in the examples at the following link:
http://spec.openapis.org/oas/v3.0.3.html#fixed-fields-14).  An example:
    override_schema={
        "/api/alert/registrations/": {
            "POST": {
                201: {
                    "properties": {
                        "message": {
                            "type": "string"
                        },
                        "id": {
                            "type": "integer"
                        }
                    }
                },
            }
        }
    }

Finally, if you still need to further customize your API schema, you can do this in the 
make_manual_schema_changes function below. This is applied to the final schema after all 
automatic changes / customizations are applied.  For more about the format of an OpenAPI 
schema (which you would need to know a bit about to make further customizations), see this
documentation:
http://spec.openapis.org/oas/v3.0.3.html
"""

openapi_description = """
# Introduction
Penn Courses ([GitHub](https://github.com/pennlabs/penn-courses">)) is the umbrella
categorization for [Penn Labs](https://pennlabs.org/)
products designed to help students navigate the course registration process. It currently
includes three products, each with their own API documented on this page:
Penn Course Alert, Penn Course Plan, and Penn Course Review.

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

# This dictionary takes app names (the string just after /api/ in the path or just after /
# if /api/ does not come at the beginning of the path)
# as values and abbreviated versions of those names as values.  It is used to
# add an abbreviated app prefix designating app membership to each route's tag name
# (allowing all the tags for each app to be organized into tag groups for each app).
subpath_abbreviations = {"plan": "PCP", "alert": "PCA", "review": "PCR", "courses": "PCx",
                         "accounts": "Accounts"}

# Tag groups organize tags into groups; they show up in the left sidebar and divide the categories
# of routes into meta categories. We are using them to separate our tags by app.
# This dictionary should map abbreviated app names (values from the dict above) to
# longer form names which will show up as the tag group name in the documentation.
tag_group_abbreviations = {
    "PCP": "Penn Course Plan",
    "PCA": "Penn Course Alert",
    "PCR": "Penn Course Review",
    "PCx": "Penn Courses (Unified)",
    "Accounts": "Penn Labs Accounts",
    "": "Other"  # Catches all other tags (this should normally be an empty tag group and if so
    # it will not show up in the documentation, but is left as a debugging safeguard).
    # If routes are showing up in a "Misc" tag in this group, make sure you set the schema for
    # those views to be PcxAutoSchema, as is instructed in the meta docs above.
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
        """
    ),
    "[PCP] Requirements": dedent(
        """
        These routes expose the academic requirements for the current semester which are stored on
        our backend (hopefully comprehensive).
        """
    ),
    "[PCP] Course": dedent(
        """
        These routes expose course information for PCP for the current semester.
        """
    ),
    "[PCA] Registration History": dedent(
        """
        These routes expose a user's registration history (including deleted registrations)
        for the current semester.
        """
    ),
    "[PCA] Registration": dedent(
        """
        As the main API endpoints for PCA, these routes allow interaction with the user's 
        PCA registrations.  An important concept which is referenced throughout the documentation 
        for these routes is that of the "resubscribe chain".  A resubscribe chain is a chain 
        of PCA registrations where the tail of the chain was an original registration created 
        through a POST request to /api/alert/registrations/ specifying a new section (one that 
        the user wasn't already registered to receive alerts for).  Each next element in the chain 
        is a registration created by resubscribing to the previous registration (once that 
        registration had triggered an alert to be sent), either manually by the user or 
        automatically if auto_resubscribe was set to true.  Then, it follows that the head of the 
        resubscribe chain is the most relevant registration for that section; if any of the 
        registrations in the chain are active, it would be the head.  And if the head is active, 
        none of the other registrations in the chain are active.
        """
    ),
    "[PCA] User": dedent(
        """
        These routes expose a user's saved settings.
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
        """
    ),
    "Miscs": dedent(
        """
        <span style="color:red;">WARNING</span>: This tag should not be used, and its existence 
        indicates you may have forgotten to set a view's schema to PcxAutoSchema for the views 
        under this tag. See the meta documentation in backend/PennCourses/docs_settings.py of our 
        codebase for instructions on how to properly set a view's schema to PcxAutoSchema.
        """
    )
}

# do not edit
labs_logo_url = "https://i.imgur.com/tVsRNxJ.png"


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

    data["info"]["x-logo"] = {"url": labs_logo_url, "altText": "Labs Logo"}
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

        # Change all the response codes in the examples_dict to strings
        # and change the methods to lower case
        global examples_dict
        for key, val in examples_dict.items():
            examples_dict[key] = {k.lower(): v for k, v in examples_dict[key].items()}
            for val2 in examples_dict[key].values():
                if "responses" in val2.keys():
                    for res in val2["responses"]:
                        if "code" in res.keys() and isinstance(res["code"], int):
                            res["code"] = str(res["code"])

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
        for path_name, val in data["paths"].items():
            for method_name, v in val.items():
                def delete_required_dfs(dictionary):
                    if not isinstance(dictionary, dict):
                        return None
                    dictionary.pop('required', None)
                    for value in dictionary.values():
                        delete_required_dfs(value)
                delete_required_dfs(v['responses'])

        # Since tags could not be updated while we were through tags above, we update them now.
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

        # Add request/response examples to the documentation (instructions on how to customize a
        # route's examples can be found above).
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
                                             f"If '[SCHEMA]' is not in the description for this path/method/code, "
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

    def __init__(self, tags=None, examples={}, response_codes={}, override_schema={}):
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
        for k, d in override_schema.items():
            override_schema[k] = {k.upper(): v for k, v in d.items()}
        self.override_schema = override_schema

        examples_dict.update(examples)

        super().__init__()

    def get_description(self, path, method):
        # Add the method and path to the description of that method/path so it is more visible.
        desc = (
            "("
            + method.upper()
            + " `"
            + path
            + "`)"
            + "  \n  \n"
        )
        # Add the description from docstrings (default functionality).
        desc += super().get_description(path, method)
        view = self.view
        # Add a note if the path/method requires user authentication.
        if IsAuthenticated in view.permission_classes:
            desc += '\n\n<span style="color:red;">User authentication required</span>.'
        return desc

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

        name = name.replace("_", " ").title()

        return name

    def get_tags(self, path, method):
        # If user has specified tags, use them.
        if self._tags:
            return self._tags

        name = self.get_name(path, method)
        path_components = (path[1:] if path.startswith("/") else path).split("/")
        subpath = path_components[1] if path_components[0] == "api" else path_components[0]
        if subpath not in subpath_abbreviations.keys():
            raise ValueError(f"You must add the the '{subpath}' subpath to the "
                             "subpath_abbreviations dict in backend/PennCourses/docs_settings.py. "
                             f"This subpath was inferred from the path '{path}'.")
        return ["[" + subpath_abbreviations[subpath] + "] " + name]

    def _get_operation_id(self, path, method):
        if (path, method) in custom_operation_id.keys():
            return custom_operation_id[(path, method)]

        action = self.get_action(path, method)
        name = self.get_name(path, method)

        if action == "list":  # listThings instead of listThing
            name = pluralize_word(name)

        ret = action + " " + name

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
                str(k): {'description': v.replace("[SCHEMA]", "")}
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
            if (
                path in self.override_schema and
                method in self.override_schema[path].keys()
            ):
                return {
                    '200': {'description': "",
                        **({'content': {
                                ct: {'schema': self.override_schema[path][method][200]}
                                for ct in self.response_media_types
                            } if 200 in self.override_schema[path][method].keys() else {
                                ct: {'schema': response_schema}
                                for ct in self.response_media_types
                            }})
                        }
                }
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
        if (
            path in self.override_schema and
            method in self.override_schema[path].keys()
        ):
            return {
                str(k): {'description': v.replace("[SCHEMA]", ""),
                    **({'content': {
                            ct: {'schema': self.override_schema[path][method][k]}
                            for ct in self.response_media_types
                        } if k in self.override_schema[path][method].keys() else {
                            ct: {'schema': response_schema}
                            for ct in self.response_media_types
                        }} if "[SCHEMA]" in v else {})}
                for k, v in self.response_codes[path][method].items()
            }
        return {
            str(k): {'description': v.replace("[SCHEMA]", ""),
                **({'content': {
                        ct: {'schema': response_schema }
                        for ct in self.response_media_types
                    }} if "[SCHEMA]" in v else {})}
            for k, v in self.response_codes[path][method].items()
        }
