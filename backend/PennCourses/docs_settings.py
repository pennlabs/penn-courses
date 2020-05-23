from rest_framework.renderers import JSONOpenAPIRenderer
import json
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.schemas.utils import is_list_view
import re

"""
This file includes code and settings for our PCx autodocumentation
(based on a Django-generated OpenAPI schema and Redoc, which formats that schema into a 
readable documentation web page).  Some useful links:
https://github.com/Redocly/redoc
https://github.com/Redocly/redoc/blob/master/docs/redoc-vendor-extensions.md#tagGroupObject
https://www.django-rest-framework.org/api-guide/schemas
A Redoc example from which many of the concepts in this file were taken from:
https://redocly.github.io/redoc/
https://github.com/Redocly/redoc/blob/master/demo/openapi.yaml

IMPORTANT NOTE: for the auto-documentation to work, you need to include the line:
schema = PcxAutoSchema()
in all views (this will allow for proper tag and operation_id generation; see below).
PcxAutoSchema (defined below) is a subclass of Django's AutoSchema,
and it makes some improvements on that class for use with Redoc 
as well as some customizations specific to the Labs PCX use-case.

Maintenence: besides including schema = PcxAutoSchema(), the only maintenance we
need to do when writing new code is including docstrings in views (see
https://www.django-rest-framework.org/coreapi/from-documenting-your-api/#documenting-your-views).
You should also try to add a description for each new tag group created automatically by the docs
(visible in the nav bar).  You can do that using the custom_tag_descriptions dictionary below.
If the auto-generated names are unsatisfactory, you can also manually change any 
operation_id, tag, or tag group name (see below).
You can update the introductory sections / readme by editing the markdown-formatted
openapi_description text below.
"""

openapi_description = """
# Introduction
Penn Courses ([GitHub](https://github.com/pennlabs/penn-courses">)) is the umbrella 
categorization for [Penn Labs](https://pennlabs.org/)
products designed to help students navigate the course registration process.  It currently 
includes three products, each with their own API documented on this page: 
Penn Course Alert, Penn Course Plan, and Penn Course Review (PCR coming soon).

See `Penn Labs Notion / Penn Courses` for more details on each of our (currently) three apps.

For instructions on how to maintain this documentation while writing code,
see the comments in `backend/PennCourses/docs_settings.py` (it is easy, and will be helpful
for maintaining Labs knowledge in spite of our high member turnover rate).

# Unified Penn Courses
By virtue of the fact that all Penn Courses products deal with, well, courses, 
it would make sense for all three products to share the same backend.

We realized the necessity of a unified backend when attempting to design a new Django backend 
for Penn Course Plan.  We like to live by the philosophy of keeping it 
[DRY](https://en.wikipedia.org/wiki/Don't_repeat_yourself), and 
PCA and PCP's data models both need to reference course and 
section information. We could have simply copied over code (a bad idea) 
or created a shared reusable Django app (a better idea) for course data, 
but each app would still need to download copies of the same data. 
Additionally, this will help us build integrations between our Courses products.

See `Penn Labs Notion / Penn Courses / Unified Penn Courses` for more details on our
codebase file structure, data models, and multi-site devops scheme.  See our 
[GitHub](https://github.com/pennlabs/penn-courses">) repo for instructions on 
installation, running in development, and loading in course data for development.
"""

subpath_abbreviations = {
    "plan": "PCP",
    "alert": "PCA",
    "review": "PCR",
    "courses": "PCx"
}

# tag groups organize tags into groups; we are using them to separate our tags by app
tag_group_abbreviations = {
    "PCP": "Penn Course Plan",
    "PCA": "Penn Course Alert",
    "PCR": "Penn Course Review",
    "PCx": "Penn Courses (Unified)"
}


# operation ids are the subitems of a tag (if you click on a tag you see them)
# tags show up in the body of the documentation and as "sections" in the menu
# tags are not to be confused with tag groups (see above description of tag groups)

# name here refers to the name underlying the operation id of the view
custom_name = {  # keys are (path, method) tuples, values are custom names
    # method is one of ("GET", "POST", "PUT", "PATCH", "DELETE")
    ("/api/alert/registrationhistory/", "GET"): "Registration History",
    ("/api/alert/registrationhistory/{id}/", "GET"): "Registration History",
}

custom_operation_id = {  # keys are (path, method) tuples, values are custom names
    # method is one of ("GET", "POST", "PUT", "PATCH", "DELETE")
    ("/api/alert/registrationhistory/", "GET"): "List Registration History",
}

custom_tag_names = {  # keys are old tag names (seen on docs), values are new tag names

}

# tag descriptions show up in the documentation below the tag name
custom_tag_descriptions = {
    # keys are tag names (after any name changes from above dicts), vals are descriptions

}


def split_camel(w):
    return re.sub("([a-z0-9])([A-Z])", lambda x: x.groups()[0] + " " + x.groups()[1], w)


def pluralize_word(s):
    return s + "s"  # naive solution because this is how it is done in DRF


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
            all_list = all([('list' in v["operationId"].lower()) for v in tag_to_dicts[tag]])
            if all_list:  # if all views in tag are lists, pluralize tag name
                tag = update_tag(tag, " ".join(tag.split(" ")[:-1] +
                                               [pluralize_word(tag.split(" ")[-1])]))
            if tag in custom_tag_names.keys():  # rename custom tags
                tag = update_tag(tag, custom_tag_names[tag])
        for k, v in changes.items():  # since tags cannot be updated while iterating through tags
            tags.remove(k)
            tags.add(v)

        tag_dict = dict()
        tag_dict["tags"] = [{"name": tag, "description": custom_tag_descriptions.get(tag, "")}
                            for tag in tags]
        tag_dict["x-tagGroups"] = [{"name": v, "tags": [t for t in tags if k in t]}
                                   for k, v in tag_group_abbreviations.items()]
        tag_dict["x-tagGroups"] = [g for g in tag_dict["x-tagGroups"] if len(g["tags"]) != 0]
        return json.dumps(dict(tag_dict, **data), indent=2).encode('utf-8')


class PcxAutoSchema(AutoSchema):
    """
    This custom subclass serves to automatically generate tags and operation ID in forms
    better for Redoc and our PCX usecase.
    It also serves to backport code for custom tags generation functionality from
    this DRF PR (which hadn't been included in a stable release when this code was written):
    https://github.com/encode/django-rest-framework/pull/7184/files
    This PR is adding the functionality outlined here in the DRF api guide:
    https://www.django-rest-framework.org/api-guide/schemas/#grouping-operations-with-tags
    Once the code from this PR is included in a stable Django release, the __init__ and
    get_operation methods below should be deleted (they will be inherited from AutoSchema).
    """

    def __init__(self, tags=None):  # allow user to specify custom tag(s)
        if tags and not all(isinstance(tag, str) for tag in tags):
            raise ValueError('tags must be a list or tuple of string.')
        self._tags = tags
        super().__init__()

    def get_operation(self, path, method):
        operation = super().get_operation(path, method)
        operation['tags'] = self.get_tags(path, method)
        return operation

    def get_action(self, path, method):  # Code taken from _get_operation_id method
        method_name = getattr(self.view, 'action', method.lower())
        if is_list_view(path, method, self.view):
            action = 'list'
        elif method_name not in self.method_mapping:
            action = method_name
        else:
            action = self.method_mapping[method.lower()]
        return action

    def get_name(self, path, method):  # Some code taken from _get_operation_id method
        if (path, method) in custom_name.keys():
            return custom_name[(path, method)]

        # Try to deduce the ID from the view's model
        model = getattr(getattr(self.view, 'queryset', None), 'model', None)
        if model is not None:
            name = model.__name__

        # Try with the serializer class name
        elif hasattr(self.view, 'get_serializer_class'):
            name = self.view.get_serializer_class().__name__
            if name.endswith('Serializer'):
                name = name[:-10]

        # Fallback to the view name
        else:
            name = self.view.__class__.__name__
            if name.endswith('APIView'):
                name = name[:-7]
            elif name.endswith('View'):
                name = name[:-4]
            elif name.lower().endswith('viewset'):
                name = name[:-7]

        # Due to camel-casing of classes and `action` being lowercase,
        # apply title in order to find if action truly comes at the end of the name
        if name.endswith(
                self.get_action(path, method).title()):  # ListView, UpdateAPIView, ThingDelete ...
            name = name[:-len(self.get_action(path, method))]

        return name

    def get_tags(self, path, method):
        # If user has specified tags, use them.
        if self._tags:
            return self._tags

        name = self.get_name(path, method)
        path_components = (path[1:] if path.startswith('/') else path).split('/')
        return [("[" + subpath_abbreviations[path_components[1]] + "] "
                 if path_components[1] in subpath_abbreviations.keys() else "")
                + name]

    def _get_operation_id(self, path, method):
        if (path, method) in custom_operation_id.keys():
            return custom_operation_id[(path, method)]

        action = self.get_action(path, method)
        name = self.get_name(path, method)

        if action == 'list':  # listThings instead of listThing
            name = pluralize_word(name)

        ret = action + name

        return split_camel(ret[0].capitalize() + ret[1:])
