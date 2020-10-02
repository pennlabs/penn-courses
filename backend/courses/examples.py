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
                            "name": "Cultural Diversity in the US",
                        },
                        {
                            "id": "H@SEAS",
                            "code": "H",
                            "school": "SEAS",
                            "semester": "2020C",
                            "name": "Humanities",
                        },
                        {
                            "id": "SS@WH",
                            "code": "SS",
                            "school": "WH",
                            "semester": "2020C",
                            "name": "Social Science",
                        },
                        {
                            "id": "example@school",
                            "code": "example",
                            "school": "school",
                            "semester": "2020C",
                            "name": "Example Requirement",
                        },
                    ],
                }
            ],
        }
    },
    "/api/courses/{semester}/requirements/": {
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
                            "name": "Cultural Diversity in the US",
                        },
                        {
                            "id": "H@SEAS",
                            "code": "H",
                            "school": "SEAS",
                            "semester": "2020C",
                            "name": "Humanities",
                        },
                        {
                            "id": "SS@WH",
                            "code": "SS",
                            "school": "WH",
                            "semester": "2020C",
                            "name": "Social Science",
                        },
                        {
                            "id": "example@school",
                            "code": "example",
                            "school": "school",
                            "semester": "2020C",
                            "name": "Example Requirement",
                        },
                    ],
                }
            ],
        }
    },
}

SectionList_examples = {
    "/api/alert/courses/": {
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "GET Section List search=CIS-120",
                    "value": [
                        {
                            "section_id": "CIS-120-001",
                            "status": "C",
                            "activity": "LEC",
                            "meeting_times": '["MWF 11:00 AM - 12:00 PM"]',
                            "instructors": ["Swapneel Sheth", "Stephan A. Zdancewic"],
                            "course_title": "Programming Languages and Techniques I",
                        },
                        {
                            "section_id": "CIS-120-002",
                            "status": "C",
                            "activity": "LEC",
                            "meeting_times": '["MWF 12:00 PM - 01:00 PM"]',
                            "instructors": ["Swapneel Sheth", "Stephan A. Zdancewic"],
                            "course_title": "Programming Languages and Techniques I",
                        },
                        {
                            "section_id": "CIS-120-201",
                            "status": "C",
                            "activity": "REC",
                            "meeting_times": '["W 12:00 PM - 01:00 PM"]',
                            "instructors": [],
                            "course_title": "Programming Languages and Techniques I",
                        },
                    ],
                }
            ],
        }
    }
}

StatusUpdateView_examples = {
    "/api/courses/statusupdate/{full_code}/": {
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "List Status Updates for section",
                    "value": [
                        {
                            "old_status": "C",
                            "new_status": "O",
                            "created_at": "2019-03-23T15:46:33.199389-04:00",
                            "alert_sent": True,
                        },
                        {
                            "old_status": "O",
                            "new_status": "C",
                            "created_at": "2019-07-30T08:32:43.831505-04:00",
                            "alert_sent": False,
                        },
                        {
                            "old_status": "C",
                            "new_status": "O",
                            "created_at": "2019-07-30T10:03:45.979133-04:00",
                            "alert_sent": True,
                        },
                    ],
                }
            ],
        }
    }
}

SectionDetail_examples = {
    "/api/courses/{semester}/sections/{full_code}/": {
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "Retrieve Section detail",
                    "value": {
                        "id": "CIS-120-001",
                        "status": "O",
                        "activity": "LEC",
                        "credits": 1.0,
                        "semester": "2020C",
                        "meetings": [
                            {"day": "F", "start": 11.0, "end": 12.0, "room": " "},
                            {"day": "M", "start": 11.0, "end": 12.0, "room": " "},
                            {"day": "W", "start": 11.0, "end": 12.0, "room": " "},
                        ],
                        "instructors": ["Swapneel Sheth", "Stephan A. Zdancewic"],
                        "course_quality": 3.4,
                        "instructor_quality": 3.2,
                        "difficulty": 3.2,
                        "work_required": 3.5,
                        "associated_sections": [
                            {"id": 1476, "activity": "REC"},
                            {"id": 1477, "activity": "REC"},
                            {"id": 1478, "activity": "REC"},
                            {"id": 1479, "activity": "REC"},
                            {"id": 1480, "activity": "REC"},
                            {"id": 1481, "activity": "REC"},
                            {"id": 1482, "activity": "REC"},
                            {"id": 1483, "activity": "REC"},
                            {"id": 1484, "activity": "REC"},
                            {"id": 1485, "activity": "REC"},
                            {"id": 1486, "activity": "REC"},
                            {"id": 1487, "activity": "REC"},
                            {"id": 1488, "activity": "REC"},
                            {"id": 1489, "activity": "REC"},
                            {"id": 1490, "activity": "REC"},
                            {"id": 1491, "activity": "REC"},
                            {"id": 1492, "activity": "REC"},
                            {"id": 1493, "activity": "REC"},
                            {"id": 1494, "activity": "REC"},
                            {"id": 1495, "activity": "REC"},
                        ],
                    },
                }
            ],
        }
    }
}

CourseDetail_examples = {
    "/api/courses/{semester}/courses/{full_code}/": {
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "Retrieve Course detail",
                    "value": {
                        "id": "CIS-192",
                        "title": "Python Programming",
                        "description": "Python is an elegant, concise, and powerful language that is useful for tasks large and small. Python has quickly become a popular language for getting things done efficiently in many in all domains: scripting, systems programming, research tools, and web development. This course will provide an introduction to this modern high-level language using hands-on experience through programming assignments and a collaborative final application development project.",  # noqa: E501
                        "semester": "2020C",
                        "prerequisites": "CIS 120 OR ESE 112",
                        "course_quality": 4,
                        "instructor_quality": 4,
                        "difficulty": 2,
                        "work_required": 2,
                        "crosslistings": [],
                        "requirements": [
                            {
                                "id": "ENG@SEAS",
                                "code": "ENG",
                                "school": "SEAS",
                                "semester": "2020C",
                                "name": "Engineering",
                            },
                            {
                                "id": "FGE@WH",
                                "code": "FGE",
                                "school": "WH",
                                "semester": "2020C",
                                "name": "Flex Gen Ed",
                            },
                        ],
                        "sections": [
                            {
                                "id": "CIS-192-001",
                                "status": "C",
                                "activity": "LEC",
                                "credits": 0.5,
                                "semester": "2020C",
                                "meetings": [{"day": "T", "start": 18.0, "end": 19.3, "room": " "}],
                                "instructors": ["Swapneel Sheth"],
                                "course_quality": 4,
                                "instructor_quality": 4,
                                "difficulty": 2,
                                "work_required": 2,
                                "associated_sections": [
                                    {"id": 1579, "activity": "REC"},
                                    {"id": 1580, "activity": "REC"},
                                ],
                            },
                            {
                                "id": "CIS-192-201",
                                "status": "C",
                                "activity": "REC",
                                "credits": 0.0,
                                "semester": "2020C",
                                "meetings": [{"day": "T", "start": 10.3, "end": 12.0, "room": " "}],
                                "instructors": ["Arun K Kirubarajan"],
                                "course_quality": 4,
                                "instructor_quality": 4,
                                "difficulty": 2,
                                "work_required": 2,
                                "associated_sections": [{"id": 1578, "activity": "LEC"}],
                            },
                            {
                                "id": "CIS-192-202",
                                "status": "C",
                                "activity": "REC",
                                "credits": 0.0,
                                "semester": "2020C",
                                "meetings": [{"day": "R", "start": 10.3, "end": 12.0, "room": " "}],
                                "instructors": ["Tong Liu"],
                                "course_quality": 4,
                                "instructor_quality": 4,
                                "difficulty": 2,
                                "work_required": 2,
                                "associated_sections": [{"id": 1578, "activity": "LEC"}],
                            },
                        ],
                    },
                }
            ],
        }
    }
}

CourseList_examples = {
    "/api/courses/{semester}/courses/": {
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "Retrieve Course detail",
                    "value": [
                        {
                            "id": "AAMW-523",
                            "title": "Narrative in Ancient Art",
                            "description": 'Art history, and its cousins in religious, social, political and literary studies, have long been fascinated with the question of narrative: how do images engage time, tell stories? These are fundamental questions for ancient Near Eastern, Egyptian and Mediterranean art history and archaeology, whose rich corpus of narrative images is rarely considered in the context of "Western" art. Relations between words and things, texts and images, were as fundamental to the ancient cultures we examine as they are to modern studies. As we weigh classic modern descriptions of narrative and narratology, we will bring to bear recent debates about how (ancient) images, things, monuments, and designed spaces engage with time, space, and event, and interact with cultural memory. We will ask "who is the story for, and why?" for public and private narratives ranging from political histories to mythological encounters. Our case studies will be drawn from the instructors\' expertise in Mesopotamian visual culture, and in the visual cultures of the larger Mediterranean world from early Greek antiquity to the Hellenistic, Roman, and Late Antique periods. One central and comparative question, for instance, is the nature of recording history in pictures and texts in the imperial projects of Assyria, Achaemenid Persia, the Hellenistic kingdoms, and Rome.',  # noqa: E501
                            "semester": "2020C",
                            "num_sections": 1,
                            "course_quality": 2,
                            "instructor_quality": 2,
                            "difficulty": 2,
                            "work_required": 2,
                        },
                        {
                            "id": "ARTH-523",
                            "title": "Narrative in Ancient Art",
                            "description": 'Art history, and its cousins in religious, social, political and literary studies, have long been fascinated with the question of narrative: how do images engage time, tell stories? These are fundamental questions for ancient Near Eastern, Egyptian and Mediterranean art history and archaeology, whose rich corpus of narrative images is rarely considered in the context of "Western" art. Relations between words and things, texts and images, were as fundamental to the ancient cultures we examine as they are to modern studies. As we weigh classic modern descriptions of narrative and narratology, we will bring to bear recent debates about how (ancient) images, things, monuments, and designed spaces engage with time, space, and event, and interact with cultural memory. We will ask "who is the story for, and why?" for public and private narratives ranging from political histories to mythological encounters. Our case studies will be drawn from the instructors\' expertise in Mesopotamian visual culture, and in the visual cultures of the larger Mediterranean world from early Greek antiquity to the Hellenistic, Roman, and Late Antique periods. One central and comparative question, for instance, is the nature of recording history in pictures and texts in the imperial projects of Assyria, Achaemenid Persia, the Hellenistic kingdoms, and Rome.',  # noqa: E501
                            "semester": "2020C",
                            "num_sections": 1,
                            "course_quality": 2,
                            "instructor_quality": 2,
                            "difficulty": 2,
                            "work_required": 2,
                        },
                    ],
                }
            ],
        }
    }
}
