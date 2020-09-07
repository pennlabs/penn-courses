# See backend/PennCourses/docs_settings.py for more info on how to format these examples files.

CourseListSearch_examples = {
    "/api/plan/courses/": {
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "GET List Courses, Filter by Search",
                    "value": [
                        {
                            "id": "CIS-120",
                            "title": "Programming Languages and Techniques I",
                            "description": "A fast-paced introduction to the fundamental concepts of programming and software design. This course assumes some previous programming experience, at the level of a high school computer science class or CIS110. (If you got at least 4 in the AP Computer Science A or AB exam, you will do great.) No specific programming language background is assumed: basic experience with any language (for instance Java, C, C++, VB, Python, Perl, or Scheme) is fine. If you have never programmed before, you should take CIS 110 first.",
                            "semester": "2020C",
                            "num_sections": 22,
                            "course_quality": 2.76,
                            "instructor_quality": 3.17,
                            "difficulty": 3.08,
                            "work_required": 3.35,
                        },
                        {
                            "id": "CIS-121",
                            "title": "Programming Languages and Techniques II",
                            "description": "This is a course about Algorithms and Data Structures using the JAVA programming language. We introduce the basic concepts about complexity of an algorithm and methods on how to compute the running time of algorithms. Then, we describe data structures like stacks, queues, maps, trees, and graphs, and we construct efficient algorithms based on these representations. The course builds upon existing implementations of basic data structures in JAVA and extends them for the structures like trees, studying the performance of operations on such structures, and theiefficiency when used in real-world applications. A large project introducing students to the challenges of software engineering concludes the course.",
                            "semester": "2020C",
                            "num_sections": 16,
                            "course_quality": 4.00,
                            "instructor_quality": 4.00,
                            "difficulty": 4.00,
                            "work_required": 4.00,
                        }
                    ]
                }
            ]
        }
    },
    "/api/plan/courses/{full_code}/": {
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "GET Course Detail",
                    "value": {
                        "id": "CIS-192",
                        "title": "Python Programming",
                        "description": "Python is an elegant, concise, and powerful language that is useful for tasks large and small. Python has quickly become a popular language for getting things done efficiently in many in all domains: scripting, systems programming, research tools, and web development. This course will provide an introduction to this modern high-level language using hands-on experience through programming assignments and a collaborative final application development project.",
                        "semester": "2020C",
                        "prerequisites": "CIS 120 OR ESE 112",
                        "course_quality": 4.00,
                        "instructor_quality": 4.00,
                        "difficulty": 2.00,
                        "work_required": 2.00,
                        "crosslistings": [],
                        "requirements": [
                            {
                                "id": "ENG@SEAS",
                                "code": "ENG",
                                "school": "SEAS",
                                "semester": "2020C",
                                "name": "Engineering"
                            },
                            {
                                "id": "FGE@WH",
                                "code": "FGE",
                                "school": "WH",
                                "semester": "2020C",
                                "name": "Flex Gen Ed"
                            }
                        ],
                        "sections": [
                            {
                                "id": "CIS-192-001",
                                "status": "O",
                                "activity": "LEC",
                                "credits": 0.5,
                                "semester": "2020C",
                                "meetings": [
                                    {
                                        "day": "T",
                                        "start": 18.0,
                                        "end": 19.3,
                                        "room": " "
                                    }
                                ],
                                "instructors": [
                                    "Swapneel Sheth"
                                ],
                                "course_quality": 4.00,
                                "instructor_quality": 4.00,
                                "difficulty": 2.00,
                                "work_required": 2.00,
                                "associated_sections": [
                                    {
                                        "id": 1579,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1580,
                                        "activity": "REC"
                                    }
                                ]
                            },
                            {
                                "id": "CIS-192-201",
                                "status": "O",
                                "activity": "REC",
                                "credits": 0.0,
                                "semester": "2020C",
                                "meetings": [
                                    {
                                        "day": "T",
                                        "start": 10.3,
                                        "end": 12.0,
                                        "room": " "
                                    }
                                ],
                                "instructors": [
                                    "Arun K Kirubarajan"
                                ],
                                "course_quality": 4.00,
                                "instructor_quality": 4.00,
                                "difficulty": 2.00,
                                "work_required": 2.00,
                                "associated_sections": [
                                    {
                                        "id": 1578,
                                        "activity": "LEC"
                                    }
                                ]
                            },
                            {
                                "id": "CIS-192-202",
                                "status": "O",
                                "activity": "REC",
                                "credits": 0.0,
                                "semester": "2020C",
                                "meetings": [
                                    {
                                        "day": "R",
                                        "start": 10.3,
                                        "end": 12.0,
                                        "room": " "
                                    }
                                ],
                                "instructors": [
                                    "Tong Liu"
                                ],
                                "course_quality": 4.00,
                                "instructor_quality": 4.00,
                                "difficulty": 2.00,
                                "work_required": 2.00,
                                "associated_sections": [
                                    {
                                        "id": 1578,
                                        "activity": "LEC"
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    }
}

ScheduleViewSet_examples = {
    "/api/plan/schedules/": {
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "GET List Schedules",
                    "value": [
                        {
                            "id": 1,
                            "sections": [
                                {
                                    "id": "CIS-120-001",
                                    "status": "O",
                                    "activity": "LEC",
                                    "credits": 1.0,
                                    "semester": "2020C",
                                    "meetings": [
                                        {
                                            "day": "F",
                                            "start": 11.0,
                                            "end": 12.0,
                                            "room": " "
                                        },
                                        {
                                            "day": "M",
                                            "start": 11.0,
                                            "end": 12.0,
                                            "room": " "
                                        },
                                        {
                                            "day": "W",
                                            "start": 11.0,
                                            "end": 12.0,
                                            "room": " "
                                        }
                                    ],
                                    "instructors": [
                                        "Swapneel Sheth",
                                        "Stephan A. Zdancewic"
                                    ],
                                    "course_quality": 2.76,
                                    "instructor_quality": 3.17,
                                    "difficulty": 3.08,
                                    "work_required": 3.35,
                                    "associated_sections": [
                                        {
                                            "id": 1476,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1477,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1478,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1479,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1480,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1481,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1482,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1483,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1484,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1485,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1486,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1487,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1488,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1489,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1490,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1491,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1492,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1493,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1494,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1495,
                                            "activity": "REC"
                                        }
                                    ]
                                },
                                {
                                    "id": "CIS-160-001",
                                    "status": "C",
                                    "activity": "LEC",
                                    "credits": 1.0,
                                    "semester": "2020C",
                                    "meetings": [
                                        {
                                            "day": "R",
                                            "start": 9.0,
                                            "end": 10.3,
                                            "room": " "
                                        },
                                        {
                                            "day": "T",
                                            "start": 9.0,
                                            "end": 10.3,
                                            "room": " "
                                        }
                                    ],
                                    "instructors": [
                                        "Rajiv C Gandhi"
                                    ],
                                    "course_quality": 2.76,
                                    "instructor_quality": 3.17,
                                    "difficulty": 3.08,
                                    "work_required": 3.35,
                                    "associated_sections": [
                                        {
                                            "id": 1538,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1539,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1540,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1541,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1542,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1543,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1544,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1545,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1546,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1547,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1548,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1549,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1550,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1551,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1552,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1553,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1554,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1555,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1556,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1557,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1558,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1559,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1560,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1561,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1562,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1563,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1564,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1565,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1566,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1567,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1568,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1569,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1570,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1571,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1572,
                                            "activity": "REC"
                                        },
                                        {
                                            "id": 1573,
                                            "activity": "REC"
                                        }
                                    ]
                                }
                            ],
                            "semester": "2020C",
                            "name": "Fall 2020 Only CIS",
                            "created_at": "2020-08-17T18:10:49.464415-04:00",
                            "updated_at": "2020-08-17T18:10:49.464451-04:00"
                        },
                    ]
                }
            ]
        },
        "POST": {
            "requests": [
                {
                    "summary": "Minimally Customized POST",
                    "value": {
                        "name": "Fall 2020 Only CIS",
                        "sections": [
                            {
                                "id": "CIS-120-001",
                                "semester": "2020C"
                            },
                            {
                                "id": "CIS-160-001",
                                "semester": "2020C"
                            }
                        ]
                    }
                },
                {
                    "summary": "Maximally Customized POST",
                    "value": {
                        "id": 14,
                        "name": "Fall 2020 Only CIS",
                        "semester": "2020C",
                        "sections": [
                            {
                                "id": "CIS-120-001",
                                "semester": "2020C"
                            },
                            {
                                "id": "CIS-160-001",
                                "semester": "2020C"
                            },
                        ]
                    }
                }
            ],
            "responses": []
        }
    },
    "/api/plan/schedules/{id}/": {
        "GET": {
            "requests": [],
            "responses": [
                {
                    "code": 200,
                    "summary": "GET Specific Schedule",
                    "value": {
                        "id": 1,
                        "sections": [
                            {
                                "id": "CIS-120-001",
                                "status": "O",
                                "activity": "LEC",
                                "credits": 1.0,
                                "semester": "2020C",
                                "meetings": [
                                    {
                                        "day": "F",
                                        "start": 11.0,
                                        "end": 12.0,
                                        "room": " "
                                    },
                                    {
                                        "day": "M",
                                        "start": 11.0,
                                        "end": 12.0,
                                        "room": " "
                                    },
                                    {
                                        "day": "W",
                                        "start": 11.0,
                                        "end": 12.0,
                                        "room": " "
                                    }
                                ],
                                "instructors": [
                                    "Swapneel Sheth",
                                    "Stephan A. Zdancewic"
                                ],
                                "course_quality": 2.76,
                                "instructor_quality": 3.17,
                                "difficulty": 3.08,
                                "work_required": 3.35,
                                "associated_sections": [
                                    {
                                        "id": 1476,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1477,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1478,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1479,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1480,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1481,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1482,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1483,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1484,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1485,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1486,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1487,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1488,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1489,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1490,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1491,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1492,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1493,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1494,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1495,
                                        "activity": "REC"
                                    }
                                ]
                            },
                            {
                                "id": "CIS-160-001",
                                "status": "C",
                                "activity": "LEC",
                                "credits": 1.0,
                                "semester": "2020C",
                                "meetings": [
                                    {
                                        "day": "R",
                                        "start": 9.0,
                                        "end": 10.3,
                                        "room": " "
                                    },
                                    {
                                        "day": "T",
                                        "start": 9.0,
                                        "end": 10.3,
                                        "room": " "
                                    }
                                ],
                                "instructors": [
                                    "Rajiv C Gandhi"
                                ],
                                "course_quality": 2.76,
                                "instructor_quality": 3.17,
                                "difficulty": 3.08,
                                "work_required": 3.35,
                                "associated_sections": [
                                    {
                                        "id": 1538,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1539,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1540,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1541,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1542,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1543,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1544,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1545,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1546,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1547,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1548,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1549,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1550,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1551,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1552,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1553,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1554,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1555,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1556,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1557,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1558,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1559,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1560,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1561,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1562,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1563,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1564,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1565,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1566,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1567,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1568,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1569,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1570,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1571,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1572,
                                        "activity": "REC"
                                    },
                                    {
                                        "id": 1573,
                                        "activity": "REC"
                                    }
                                ]
                            }
                        ],
                        "semester": "2020C",
                        "name": "Fall 2020 Only CIS",
                        "created_at": "2020-08-17T18:10:49.464415-04:00",
                        "updated_at": "2020-08-17T18:10:49.464451-04:00"
                    }
                }
            ]
        },
        "PUT": {
            "requests": [
                {
                    "summary": "Minimally Customized PUT",
                    "value": {
                        "name": "Fall 2020 Only CIS New",
                        "sections": [
                            {
                                "id": "CIS-120-002",
                                "semester": "2020C"
                            },
                            {
                                "id": "CIS-160-002",
                                "semester": "2020C"
                            },
                        ]
                    }
                },
                {
                    "summary": "Maximally Customized PUT",
                    "value": {
                        "name": "Fall 2020 Only CIS New",
                        "semester": "2020C",
                        "sections": [
                            {
                                "id": "CIS-120-002",
                                "semester": "2020C"
                            },
                            {
                                "id": "CIS-160-002",
                                "semester": "2020C"
                            },
                        ]
                    }
                }
            ],
            "responses": []
        }
    }
}
