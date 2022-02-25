import jellyfish

from courses.models import Course
import re
from itertools import zip_longest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from plan.management.commands.trainrecommender import get_descriptions, vectorize_courses_by_description

def link_courses(full_code1, full_code2, crosswalk, prompt = True, threshold=.95):
    """
    Check if two courses belong to the same topic and links their topics if they do.

    Two courses have their topics linked if they have a matching course code, or
     are mapped in the crosswalk (which is mapping of new -> course codes), or
     the user elects to link them after prompting (see below)

    The user is prompted if the course has not been automatically linked, the title
     is effectively identical, or the description and title are sufficiently similar.

    Otherwise the topics are not linked.
    """

    course1 = Course.objects.get(full_code1)
    course2 = Course.objects.get(full_code2)
    if full_code1 == full_code2 || course1.title == course2.title:
        return link_course_topics(course1, course2)
    elif prompt and check_course_similarity(course1, course2) >= threshold:
        if suggest_course_merge(course1, course2):
            return link_course_topics(course1, course2)
    # Create course topics if not already existent?



def link_course_topics(course1: Course, course2: Course):
    pass

def title_special_case_heuristics(title1, title2):
    """
    Handle special cases.
    1. Identify if a course title is different only by a single roman numeral or digit:
       ie CIS-120 is "Programming Languages and Techniques I" and CIS-121 is
       "Programming Languages and Techniques II", and split if this is true
    """
    title1, title2 = title1.strip(), title2.strip()
    # Case 1
    sequels_regex = re.compile("(\d|IX|IV|V?I{0,3})")
    splits = zip_longest(re.split(sequels_regex, title1), re.split(sequels_regex, title2))
    previous_split = None;
    for i, split1, split2 in enumerate(splits):
        if i % 2 == 0:
            previous_split = split1 == split2
        else:
            if split1 != split2 and previous_split:
                return False
    return True

def lev_divided_by_avg_title_length(title1, title2):
    """
    Compute levenshtein distance between 2 titles and then divide by avg title length.
    """
    if title1 is np.NaN or title2 is np.NaN:
        return 0.0
    return 2 * jellyfish.levenshtein_distance(title1, title2) / (len(title1) + len(title2))

def check_course_similarity(course1: Course, course2: Course, vectorizer):
    """
    Compute similarity metric (normalized to 0-1) based on titles, descriptions
    """
    if course1.title == course2.title:
        return 1.0
    normalized_title_metric = 1.0 - lev_divided_by_avg_title_length(course1.title, course2.title)
    if normalized_title_metric < .3:
        return 0.0

    normalized_description_metric = cosine_similarity(
        vectorize_courses_by_description(get_descriptions(Course.objects.all()))
    )




def suggest_course_merge(course1, course2):
    course1.prerequisites == course2.prerequisites
    print(
        f"""
        Merge {course1.full_code} ({course1.semester}) and {course2.full_code} ({course2.semester})?
        Title1          : {course1.title, course2.title}?
        Title Sim.      :
        Description1    : {course1.description}
        Description2    : {course2.description}
        Description Sim.: 
        Prereqs1        : {course1.prerequisites}
        Prereqs2        : {course2.prerequisites}
        """
    )
    if input("Merge? Y/N").lower().split() == "y":
        return True
    return False
