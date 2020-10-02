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
                },
                {
                    "code": 200,
                    "summary": "POST With ID to Update",
                    "value": {
                        "id": 1,
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
                            "section_status": "C"
                        }
                    ]
                }
            ]
        }
    },
    "/api/alert/registrations/{id}/": {
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "Get Registration Detail",
                    "value": {
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
                        "section_status": "C"
                    }
                }
            ]
        },
        "PUT": {
            "requests": [
                {
                    "code": 200,
                    "summary": "Resubscribe",
                    "value": {
                        "resubscribe": True,
                    }
                },
                {
                    "code": 200,
                    "summary": "Modify Auto-Resubscribe",
                    "value": {
                        "auto_resubscribe": True,
                    }
                },
                {
                    "code": 200,
                    "summary": "Cancel Registration",
                    "value": {
                        "cancelled": True
                    }
                },
                {
                    "code": 200,
                    "summary": "Delete Registration",
                    "value": {
                        "deleted": True
                    }
                },
            ],
            "responses": []
        }
    },
    "/api/alert/registrationhistory/": {
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "List Registration History",
                    "value": [
                        {
                            "id": 1,
                            "created_at": "2020-10-02T03:29:47.858281-04:00",
                            "original_created_at": "2020-10-02T03:29:47.858281-04:00",
                            "updated_at": "2020-10-02T04:55:31.357455-04:00",
                            "section": "CIS-120-001",
                            "user": "mureytasroc",
                            "deleted": True,
                            "auto_resubscribe": True,
                            "notification_sent": False,
                            "notification_sent_at": None,
                            "deleted_at": "2020-10-02T04:55:31.355307-04:00",
                            "is_active": False,
                            "section_status": "C"
                        },
                        {
                            "id": 2,
                            "created_at": "2020-10-02T04:56:22.916370-04:00",
                            "original_created_at": "2020-10-02T04:56:22.916370-04:00",
                            "updated_at": "2020-10-02T04:56:35.658996-04:00",
                            "section": "CIS-120-001",
                            "user": "mureytasroc",
                            "deleted": False,
                            "auto_resubscribe": False,
                            "notification_sent": False,
                            "notification_sent_at": None,
                            "deleted_at": None,
                            "is_active": False,
                            "section_status": "C"
                        },
                        {
                            "id": 3,
                            "created_at": "2020-10-02T04:56:46.885910-04:00",
                            "original_created_at": "2020-10-02T04:56:22.916370-04:00",
                            "updated_at": "2020-10-02T04:56:46.888007-04:00",
                            "section": "CIS-120-001",
                            "user": "mureytasroc",
                            "deleted": False,
                            "auto_resubscribe": False,
                            "notification_sent": False,
                            "notification_sent_at": None,
                            "deleted_at": None,
                            "is_active": True,
                            "section_status": "C"
                        }
                    ]
                }
            ]
        }
    },
    "/api/alert/registrationhistory/{id}/": {
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "Retrieve Registration History Detail",
                    "value": {
                        "id": 1,
                        "created_at": "2020-10-02T03:29:47.858281-04:00",
                        "original_created_at": "2020-10-02T03:29:47.858281-04:00",
                        "updated_at": "2020-10-02T04:55:31.357455-04:00",
                        "section": "CIS-120-001",
                        "user": "mureytasroc",
                        "deleted": True,
                        "auto_resubscribe": True,
                        "notification_sent": False,
                        "notification_sent_at": None,
                        "deleted_at": "2020-10-02T04:55:31.355307-04:00",
                        "is_active": False,
                        "section_status": "C"
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
