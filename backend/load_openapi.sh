#!/usr/bin/env bash

./manage.py generateschema > openapi/openapi.yaml
./patchyaml.py -b openapi/openapi.yaml -p openapi/patch_*.yaml -o openapi/openapi.yaml
