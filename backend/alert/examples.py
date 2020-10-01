# See backend/PennCourses/docs_settings.py for more info on how to format these examples files.

RegistrationViewSet_examples = {
    "/api/alert/registrations/": {
        "POST": {
            "requests": [
                {
                    "summary": "Minimally Customized POST",
                    "value": {
                        "section": "CIS-120-001"
                    }
                },
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
}

RegistrationViewSet_override_schema = {
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
