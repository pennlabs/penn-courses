# See backend/PennCourses/docs_settings.py for more info on how to format these examples files.

RequirementList_examples = {
    "/api/plan/requirements/": {
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "GET List Requirements",
                    "value": [
                        {
                            "id": "MC2@SAS",
                            "code": "MC2",
                            "school": "SAS",
                            "semester": "2020C",
                            "name": "Cultural Diversity in the US"
                        },
                        {
                            "id": "H@SEAS",
                            "code": "H",
                            "school": "SEAS",
                            "semester": "2020C",
                            "name": "Humanities"
                        },
                        {
                            "id": "SS@WH",
                            "code": "SS",
                            "school": "WH",
                            "semester": "2020C",
                            "name": "Social Science"
                        },
                        {
                            "id": "example@school",
                            "code": "example",
                            "school": "school",
                            "semester": "2020C",
                            "name": "Example Requirement"
                        }
                    ]
                }
            ]
        }
    }
}


