from courses.models import Section
from review.models import REVIEW_BIT_LABEL
from review.util import to_r_camel


ACTIVITY_CHOICES = dict(Section.ACTIVITY_CHOICES)
ACTIVITY_CHOICES["***"] = None

# Unless you are looking to modify documentation, it is probably easier to view this
# documentation at localhost:8000/api/documentation/ in the PCR section, rather than
# reading through this file

EXPANDED_REVIEW_BIT_LABEL = tuple(
    list(REVIEW_BIT_LABEL)
    + [
        (
            "RFINALENROLLMENT",
            "Final Enrollment at the End of the Semester",
            "final_enrollment",
        ),
        ("RPERCENTOPEN", "Percent of Add/Drop Period Open", "percent_open"),
        ("RNUMOPENINGS", "Number of Openings During Add/Drop", "num_openings"),
        (
            "RFILLEDINADVREG",
            "Percent of Sections Completely Filled During Advance Registration",
            "filled_in_adv_reg",
        ),
    ]
)

course_review_aggregation_schema = {
    # This dict contains the schema of the "_reviews" fields returned in course review views
    **{
        "rSemesterCalc": {
            "type": "string",
            "description": "The oldest semester included in these review aggregations (of the form YYYYx where x is A [for spring], B [summer], or C [fall]), e.g. `2019C` for fall 2019. This field will not be missing.",  # noqa E501
        },
        "rSemesterCount": {
            "type": "integer",
            "description": "The number of semesters included in these review aggregations. This field will not be missing.",  # noqa E501
        },
    },
    **{
        to_r_camel(bit_label[2]): {
            "type": "number",
            "description": f"Average {bit_label[1]}",
        }
        for bit_label in EXPANDED_REVIEW_BIT_LABEL
    },
}

plots_schema = {
    "pca_demand_plot": {
        "type": "array",
        "description": (
            "The plot of average relative pca demand for sections (excluding non-primary "
            "crosslisted sections) of this topic over time during historical add/drop periods. "
            "It is an array of pairs (2-length arrays), "
            "with each pair of the form `[percent_through, relative_pca_demand]`. The "
            "`percent_through` value is a float in the range [0,1], and represents percentage "
            "through the add/drop period. The `relative_pca_demand` value is a float in the "
            "range [0,1], and represents the average of the relative pca demands of all primary "
            "sections of this topic, at that point in time. The first item of each pair "
            "should be plotted on the x-axis and the second item should be plotted on the "
            "y-axis. Note that floating point imprecision may cause "
            "some of the percent_through values to be slightly off (like 0.35000000000000003), "
            "so you should round if you display these data as strings anywhere. "
            "This field will not be missing. However, this field will be null if there are no "
            "underlying sections with [no permit required for registration] and [valid data]."
        ),
    },
    "pca_demand_plot_since_semester": {
        "type": "string",
        "description": (
            "The earliest semester from which data is taken for the PCA demand plot given in the "
            "`pca_demand_plot` field."
        ),
    },
    "pca_demand_plot_num_semesters": {
        "type": "integer",
        "description": (
            "The number of semesters from which data is taken for the PCA demand plot given in the "
            "`pca_demand_plot` field."
        ),
    },
    "percent_open_plot": {
        "type": "array",
        "description": (
            "The plot of percentage of sections (excluding non-primary crosslisted sections) of "
            "this topic that were open at each point in time during historical add/drop periods. "
            "It is an array of pairs (2-length arrays), with each pair of the form "
            "`[percent_through, percent_open]`. The `percent_through` value is a float in the "
            "range [0,1], and represents percentage through the add/drop period. "
            "The `percent_open` value is a float in the range [0,1], and represents "
            "the percent of sections of this course that were open (excluding non-primary "
            "crosslisted sections), at that point in time. The first item of each pair "
            "should be plotted on the 'x-axis' and the second item should be plotted on the "
            "'y-axis'. Note that floating point imprecision may cause "
            "some values to be slightly off (like 0.35000000000000003), "
            "so you should round if you display these data as strings anywhere. "
            "This field will not be missing. However, this field will be null if there are no "
            "underlying sections with [no permit required for registration] and [valid data]."
        ),
    },
    "percent_open_plot_since_semester": {
        "type": "string",
        "description": (
            "The earliest semester from which data is taken for the percent open plot given in the "
            "`percent_open_plot` field."
        ),
    },
    "percent_open_plot_num_semesters": {
        "type": "integer",
        "description": (
            "The number of semesters from which data is taken for the percent open plot given in "
            "the `percent_open_plot` field."
        ),
    },
}

instructor_review_aggregation_schema = {
    # This dict contains the schema of the "_reviews" fields returned in the
    # course-specific instructor review aggregation object within the response returned by
    # course review views
    to_r_camel(bit_label[2]): {
        "type": "number",
        "description": f"Average {bit_label[1]}",
    }
    for bit_label in EXPANDED_REVIEW_BIT_LABEL
}

course_reviews_response_schema = {
    "course-reviews": {
        "GET": {
            200: {
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The dash-joined department and most-recent code of this course, e.g. `CIS-1200`.",  # noqa E501
                    },
                    "last_offered_sem_if_superceded": {
                        "type": "string",
                        "description": "The last semester in which this course was offered, if it has been superseded by a more recent course (with the same full code).",  # noqa E501
                    },
                    "aliases": {
                        "type": "array",
                        "description": "A list of courses that are crosslisted with this course (each represented by its dash-joined department and code).",  # noqa E501
                        "items": {
                            "type": "string",
                        },
                    },
                    "historical_codes": {
                        "description": "The historical lineage of primary course codes that have represented this course (from most recent to oldest).",  # noqa E501
                        "items": {
                            "type": "object",
                            "properties": {
                                "full_code": {
                                    "type": "string",
                                    "description": "The dash-joined department and course code.",
                                },
                                "branched_from": {
                                    "type": "boolean",
                                    "description": "A flag indicating whether this code was branched into multiple new codes (e.g. in fall 2022). In these cases we should link to the old course on PCR because its reviews will not be included on the same page (unlike linear links).",  # noqa E501
                                },
                                "semester": {
                                    "type": "string",
                                    "description": "The most recent semester this code was used (of the form YYYYx where x is A [for spring], B [summer], or C [fall]), e.g. `2022C` for fall 2022.",  # noqa E501
                                },
                            },
                        },
                    },
                    "name": {
                        "type": "string",
                        "description": "The title of the course, e.g. 'Programming Languages and Techniques I' for CIS-120.",  # noqa E501
                    },
                    "description": {
                        "type": "string",
                        "description": "The description of the course, e.g. 'A fast-paced introduction to the fundamental concepts of programming... [etc.]' for CIS-120.",  # noqa E501
                    },
                    "latest_semester": {
                        "type": "string",
                        "description": "The most recent semester this course was offered (of the form YYYYx where x is A [for spring], B [summer], or C [fall]), e.g. `2022C` for fall 2022.",  # noqa E501
                    },
                    "registration_metrics": {
                        "type": "boolean",
                        "description": "True if this course has registration metrics that you can access via the Retrieve Plots route.",  # noqa E501
                    },
                    "num_sections": {
                        "type": "integer",
                        "description": "The number of sections belonging to this course (excluding non-primary crosslisted sections) across all semesters (that we have data for).",  # noqa E501
                    },
                    "num_sections_recent": {
                        "type": "integer",
                        "description": "The number of sections belonging to this course (excluding non-primary crosslisted sections) in its most recent semester.",  # noqa E501
                    },
                    "average_reviews": {
                        "type": "object",
                        "description": "This course's average reviews across all of its sections (excluding non-primary crosslisted sections) from all semesters. Note that if any of these subfields are missing or null, that means the subfield is not applicable or missing from our data (you should check for null values).",  # noqa E501
                        "properties": course_review_aggregation_schema,
                    },
                    "recent_reviews": {
                        "type": "object",
                        "description": "This course's average reviews across all of its sections (excluding non-primary crosslisted sections) from the most recent semester. Note that if any of these subfields are missing or null, that means the subfield is not applicable or missing from our data (you should check for null values).",  # noqa E501
                        "properties": course_review_aggregation_schema,
                    },
                    "num_semesters": {
                        "type": "integer",
                        "description": "The number of semesters for which this course has been taught (that we have data for).",  # noqa E501
                    },
                    "instructors": {
                        "type": "object",
                        "description": "Reviews for this course broken down by instructor. Note that each key in this subdictionary is a stringified instructor id (indicated by `STRINGIFIED_INSTRUCTOR_ID`; this is not an actual key but a placeholder for potentially many keys).",  # noqa E501
                        "properties": {
                            "STRINGIFIED_INSTRUCTOR_ID": {
                                "type": "object",
                                "description": "This key `STRINGIFIED_INSTRUCTOR_ID` is a placeholder for potentially many stringified instructor id keys.",  # noqa E501
                                "properties": {
                                    "id": {
                                        "type": "integer",
                                        "description": "The integer id of this instructor; note that this is just the int version of this subdictionary's key in the parent dictionary.",  # noqa E501
                                    },
                                    "average_reviews": {
                                        "type": "object",
                                        "description": "This instructor's average reviews across all of the sections of this course that he/she has taught. Note that if any of these subfields are missing or null, that means the subfield is not applicable or missing from our data (you should check for null values).",  # noqa E501
                                        "properties": instructor_review_aggregation_schema,
                                    },
                                    "recent_reviews": {
                                        "type": "object",
                                        "description": "This instructor's average reviews across all of the sections of this course that he/she has taught in his/her most recent semester teaching this course that has review data. Note that if any of these subfields are missing or null, that means the subfield is not applicable or missing from our data (you should check for null values).",  # noqa E501
                                        "properties": instructor_review_aggregation_schema,
                                    },
                                    "latest_semester": {
                                        "type": "string",
                                        "description": "The most recent semester this instructor taught this course (of the form YYYYx where x is A [for spring], B [summer], or C [fall]), e.g. `2019C` for fall 2019.",  # noqa E501
                                    },
                                    "num_semesters": {
                                        "type": "integer",
                                        "description": "The number of semesters that this instructor has taught this course (that we have data for).",  # noqa E501
                                    },
                                    "name": {
                                        "type": "string",
                                        "description": "The instructor's name",
                                    },
                                },
                            }
                        },
                    },
                }
            },
        }
    },
}

course_plots_response_schema = {
    "course-plots": {
        "GET": {
            200: {
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The dash-joined department and most-recent (across all codes representing the topic) code of the course, e.g. `CIS-120` for CIS-120.",  # noqa E501
                    },
                    "current_add_drop_period": {
                        "type": "object",
                        "description": "The start and end dates of the upcoming/current semester's add/drop period",  # noqa E501
                        "properties": {
                            "start": {
                                "type": "string",
                                "description": "A string datetime representation of the start of the current/upcoming add/drop period.",  # noqa E501
                            },
                            "end": {
                                "type": "string",
                                "description": "A string datetime representation of the end of the current/upcoming add/drop period.",  # noqa E501
                            },
                        },
                    },
                    "average_plots": {
                        "type": "object",
                        "description": "This course's plots (PCA demand, percent sections open), averaged across all of its sections from all semesters. Note that if any of these subfields are missing or null, that means the subfield is not applicable or missing from our data (you should check for null values).",  # noqa E501
                        "properties": course_review_aggregation_schema,
                    },
                    "recent_plots": {
                        "type": "object",
                        "description": "This course's plots (PCA demand, percent sections open), averaged across all of its sections from the most recent semester before the current semester. Note that if any of these subfields are missing or null, that means the subfield is not applicable or missing from our data (you should check for null values).",  # noqa E501
                        "properties": course_review_aggregation_schema,
                    },
                }
            },
        }
    },
}

instructor_reviews_response_schema = {
    "instructor-reviews": {
        "GET": {
            200: {
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The full name of the instructor.",
                    },
                    "num_sections_recent": {
                        "type": "integer",
                        "description": "The number of sections this instructor taught in his/her most recent semester teaching.",  # noqa E501
                    },
                    "num_sections": {
                        "type": "integer",
                        "description": "The number of sections this instructor has taught (that we have data for).",  # noqa E501
                    },
                    "average_reviews": {
                        "type": "object",
                        "description": "This instructor's average reviews across all of his/her taught sections from all semesters. Note that if any of these subfields are missing or null, that means the subfield is not applicable or missing from our data (you should check for null values).",  # noqa E501
                        "properties": instructor_review_aggregation_schema,
                    },
                    "recent_reviews": {
                        "type": "object",
                        "description": "This instructor's average reviews across all of his/her taught sections from only his/her most recent semester teaching that has review data. Note that if any of these subfields are missing or null, that means the subfield is not applicable or missing from our data (you should check for null values).",  # noqa E501
                        "properties": instructor_review_aggregation_schema,
                    },
                    "num_semesters": {
                        "type": "integer",
                        "description": "The number of semesters this instructor has taught (that we have data for).",  # noqa E501
                    },
                    "courses": {
                        "type": "object",
                        "description": "Reviews for this instructor broken down by the courses he/she has taught. Note that each key in this subdictionary is the course full code (indicated by `COURSE_FULL_CODE`; this is not an actual key but a placeholder for potentially many keys).",  # noqa E501
                        "properties": {
                            "COURSE_FULL_CODE": {
                                "type": "object",
                                "description": "This key `COURSE_FULL_CODE` is a placeholder for potentially many course full code keys. Each full code is the dash-joined department and most-recent (across all codes representing the topic) code of the course, e.g. `CIS-120` for CIS-120.",  # noqa E501
                                "properties": {
                                    "full_code": {
                                        "type": "string",
                                        "description": "The dash-joined department and most-recent (across all codes representing the topic) code of the course, e.g. `CIS-120` for CIS-120.",  # noqa E501
                                    },
                                    "average_reviews": {
                                        "type": "object",
                                        "description": "This course's average reviews across all of its sections taught by this instructor from all semesters. Note that if any of these subfields are missing or null, that means the subfield is not applicable or missing from our data (you should check for null values).",  # noqa E501
                                        "properties": course_review_aggregation_schema,
                                    },
                                    "recent_reviews": {
                                        "type": "object",
                                        "description": "This course's average reviews across all of its sections taught by this instructor from the most recent semester. Note that if any of these subfields are missing or null, that means the subfield is not applicable or missing from our data (you should check for null values).",  # noqa E501
                                        "properties": course_review_aggregation_schema,
                                    },
                                    "latest_semester": {
                                        "type": "string",
                                        "description": "The most recent semester this course was taught by this instructor (of the form YYYYx where x is A [for spring], B [summer], or C [fall]), e.g. `2019C` for fall 2019.",  # noqa E501
                                    },
                                    "num_semesters": {
                                        "type": "integer",
                                        "description": "The number of semesters in which this course was taught by this instructor (that we have data for).",  # noqa E501
                                    },
                                    "code": {
                                        "type": "string",
                                        "description": "Same as `full_code`.",
                                    },
                                    "name": {
                                        "type": "string",
                                        "description": "The title of the course, e.g. 'Programming Languages and Techniques I' for CIS-120.",  # noqa E501
                                    },
                                },
                            }
                        },
                    },
                }
            }
        }
    }
}

autocomplete_response_schema = {
    "review-autocomplete": {
        "GET": {
            200: {
                "properties": {
                    "courses": {
                        "type": "array",
                        "description": "Data on courses for autocomplete.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "The dash-joined department and code of the course, e.g. `CIS-120` for CIS-120.",  # noqa E501
                                },
                                "desc": {
                                    "type": "string",
                                    "description": "The title of the course, e.g. 'Programming Languages and Techniques I' for CIS-120.",  # noqa E501
                                },
                                "url": {
                                    "type": "url",
                                    "description": "The relative route through which this course's reviews can be accessed (a prefix of `/api/review/` is assumed).",  # noqa E501
                                },
                            },
                        },
                    },
                    "departments": {
                        "type": "array",
                        "description": "Data on departments for autocomplete.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "The string department code, e.g. `CIS` for the CIS department.",  # noqa E501
                                },
                                "desc": {
                                    "type": "string",
                                    "description": "The name of the department, e.g. 'Computer and Information Sci' for the CIS department.",  # noqa E501
                                },
                                "url": {
                                    "type": "url",
                                    "description": "The relative route through which this department's reviews can be accessed (a prefix of `/api/review/` is assumed).",  # noqa E501
                                },
                            },
                        },
                    },
                    "instructors": {
                        "type": "array",
                        "description": "Data on instructors for autocomplete.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "The full name of the instructor.",
                                },
                                "desc": {
                                    "type": "string",
                                    "description": "A comma-separated string list of department codes to which this instructor belongs.",  # noqa E501
                                },
                                "url": {
                                    "type": "url",
                                    "description": "The relative route through which this instructor's reviews can be accessed (a prefix of `/api/review/` is assumed).",  # noqa E501
                                },
                            },
                        },
                    },
                }
            }
        }
    }
}

department_reviews_response_schema = {
    "department-reviews": {
        "GET": {
            200: {
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The department code, e.g. `CIS` for the CIS department.",
                    },
                    "name": {
                        "type": "string",
                        "description": "The name of the department, e.g. 'Computer and Information Sci' for the CIS department.",  # noqa E501
                    },
                    "courses": {
                        "type": "object",
                        "description": "Reviews for this department broken down by its courses. Note that each key in this subdictionary is the course full code (indicated by `COURSE_FULL_CODE`; this is not an actual key but a placeholder for potentially many keys).",  # noqa E501
                        "properties": {
                            "COURSE_FULL_CODE": {
                                "type": "object",
                                "description": "This key `COURSE_FULL_CODE` is a placeholder for potentially many course full code keys. Each full code is the dash-joined department and most-recent (across all codes representing the topic) code of the course, e.g. `CIS-120` for CIS-120.",  # noqa E501
                                "properties": {
                                    "id": {
                                        "type": "string",
                                        "description": "The dash-joined department and most-recent (across all codes representing the topic) code of the course, e.g. `CIS-120` for CIS-120.",  # noqa E501
                                    },
                                    "average_reviews": {
                                        "type": "object",
                                        "description": "This course's average reviews across all of its sections from all semesters. Note that if any of these subfields are missing or null, that means the subfield is not applicable or missing from our data (you should check for null values).",  # noqa E501
                                        "properties": course_review_aggregation_schema,
                                    },
                                    "recent_reviews": {
                                        "type": "object",
                                        "description": "This course's average reviews across all of its sections from the most recent semester. Note that if any of these subfields are missing or null, that means the subfield is not applicable or missing from our data (you should check for null values).",  # noqa E501
                                        "properties": course_review_aggregation_schema,
                                    },
                                    "latest_semester": {
                                        "type": "string",
                                        "description": "The most recent semester this course was taught (of the form YYYYx where x is A [for spring], B [summer], or C [fall]), e.g. `2019C` for fall 2019.",  # noqa E501
                                    },
                                    "num_semesters": {
                                        "type": "integer",
                                        "description": "The number of semesters this class has been taught (that we have data for).",  # noqa E501
                                    },
                                    "code": {
                                        "type": "string",
                                        "description": "Same as `id`.",
                                    },
                                    "name": {
                                        "type": "string",
                                        "description": "The title of the course, e.g. 'Programming Languages and Techniques I' for CIS-120.",  # noqa E501
                                    },
                                },
                            }
                        },
                    },
                }
            }
        }
    }
}

instructor_for_course_reviews_response_schema = {
    "course-history": {
        "GET": {
            200: {
                "properties": {
                    "instructor": {
                        "type": "object",
                        "description": "Information about the instructor.",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "description": "The integer id of the instructor.",
                            },
                            "name": {
                                "type": "string",
                                "description": "The full name of the instructor.",
                            },
                        },
                    },
                    "course_code": {
                        "type": "string",
                        "description": "The dash-joined department and most-recent (across all codes representing the topic) code of the course, e.g. `CIS-120` for CIS-120.",  # noqa E501
                    },
                    "sections": {
                        "type": "array",
                        "description": "The sections of this course taught by this instructor.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "course_code": {
                                    "type": "string",
                                    "description": "The dash-joined department and course code of the section, `CIS-120` for CIS-120-001.",  # noqa E501
                                },
                                "course_name": {
                                    "type": "string",
                                    "description": "The title of the section's course, e.g. 'Programming Languages and Techniques I' for CIS-120-001.",  # noqa E501
                                },
                                "activity": {
                                    "type": "string",
                                    "description": f"The activity of the section. Options: `{str(list(dict(ACTIVITY_CHOICES).values()))}`",  # noqa E501
                                },
                                "semester": {
                                    "type": "string",
                                    "description": "The semester this section was taught (of the form YYYYx where x is A [for spring], B [summer], or C [fall]), e.g. `2019C` for fall 2019.",  # noqa E501
                                },
                                "forms_returned": {
                                    "type": "integer",
                                    "description": "The number of review responses collected for this section (or null if this section does not have review data).",  # noqa E501
                                },
                                "forms_produced": {
                                    "type": "integer",
                                    "description": "The final enrollment of this section (or null if this section does not have review data).",  # noqa E501
                                },
                                "ratings": {
                                    "type": "object",
                                    "description": "The reviews for this section.",
                                    "properties": course_review_aggregation_schema,
                                },
                                "comments": {
                                    "type": "string",
                                    "description": "A textual description of the section, as well as common sentiment about it from reviews.",  # noqa E501
                                },
                            },
                        },
                    },
                }
            }
        }
    }
}
