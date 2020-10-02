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
        },
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "Registration Created Successfully",
                    "value": [
                        {
                            "id": 1,
                            "created_at": "2020-09-27T03:13:08.813629-04:00",
                            "original_created_at": "2020-09-27T03:13:08.813629-04:00",
                            "updated_at": "2020-09-27T03:13:08.815465-04:00",
                            "section": "CIS-120-001",
                            "user": "mureytasroc",
                            "deleted": False,
                            "auto_resubscribe": False,
                            "notification_sent": False,
                            "notification_sent_at": None,
                            "deleted_at": None,
                            "is_active": True,
                            "section_status": "O"
                        }
                    ]
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
