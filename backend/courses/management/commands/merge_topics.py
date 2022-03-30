import logging
import re
from enum import Enum, auto
from itertools import zip_longest

import jellyfish
import numpy as np
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm

from courses.models import Topic


class ShouldLinkCoursesResponse(Enum):
    DEFINITELY = auto()
    MAYBE = auto()
    NO = auto()


MODEL = SentenceTransformer("all-MiniLM-L6-v2")


def prompt_for_link(course1, course2):
    """
    Prompts the user to confirm or reject a possible link between courses.
    Returns a boolean representing whether the courses should be linked.
    """
    print("\n\n============>\n")
    print(course1.full_str())
    print("\n")
    print(course2.full_str())
    print("\n<============")
    prompt = input("Should the above 2 courses be linked? (y/N) ")
    print("\n\n")
    return prompt.strip().upper() == "Y"


def should_link_courses(course_a, course_b, verbose=True):
    """
    Checks if the two courses should be linked, based on information about those
    courses stored in our database. Prompts for user input in the case of possible links,
    if in verbose mode (otherwise just logs possible links).
    Returns a response in the form of a ShouldLinkCoursesResponse enum.
    """
    if course_a.full_code == course_b.full_code or any(
        course_ac.full_code == course_b.full_code for course_ac in course_a.crosslistings
    ):
        return ShouldLinkCoursesResponse.DEFINITELY
    elif course_a.semester == course_b.semester:
        return ShouldLinkCoursesResponse.NO
    elif courses_similar(course_a, course_b):
        if verbose and prompt_for_link(course_a, course_b):
            return ShouldLinkCoursesResponse.DEFINITELY
        if not verbose:
            # Log possible link
            logging.info(f"Found possible link between {course_a} and {course_b}")
        return ShouldLinkCoursesResponse.MAYBE
    return ShouldLinkCoursesResponse.NO


def lev_divided_by_avg_title_length(title1, title2):
    """
    Compute levenshtein distance between 2 titles and then divide by avg title length.
    """
    if title1 is np.NaN or title2 is np.NaN:
        return 0.0
    return 2 * jellyfish.levenshtein_distance(title1, title2) / (len(title1) + len(title2))


def title_special_case_heuristics(title1, title2):
    """
    Handle special cases and return True if they occur, False otherwise.
    1.  Identify if a course title is different only by a single roman numeral or digit:
        ie CIS-120 is "Programming Languages and Techniques I" and CIS-121 is
        "Programming Languages and Techniques II". The specific means of doing
        this is to check if the segment directly preceding a roman numeral or
        number is identical. If it is then the title falls into this case.
    2.  Identify if a course differs by "beginner, intermediate, or advanced" at
        the start of the title (or synonyms for each respective word). Note
        additional levels like "Advanced intermediate" only have their first
        word (e.g., "Advanced") considered. Note also that if one title doesn't
        have such a first word, but the other does, False is returned.
    """
    title1, title2 = title1.strip().lower(), title2.strip().lower()
    # Case 1
    sequels_regex = re.compile(r"(\d|IX|IV|V?I{0,3})")
    splits = zip_longest(re.split(sequels_regex, title1), re.split(sequels_regex, title2))
    previous_split = None
    for i, split1, split2 in enumerate(splits):
        if i % 2 == 0:
            previous_split = split1 == split2
        else:
            if split1 != split2 and previous_split:
                return False
    # Case 2
    levels = {
        "introductory": 0,
        "beginner": 0,
        "elementary": 0,
        "intermediate": 1,
        "advanced": 2,
    }
    level1 = levels.get(title1.split()[0])
    level2 = levels.get(title2.split()[0])
    if level1 != level2:
        return False
    return True


def description_special_case_heuristics(desc1, desc2):
    """
    Handle special cases (specifically when the description is non-informative because it does not
    contain course-specific content) and return True if they occur, False otherwise.
    1. Identify if either description is of the form "topics may vary" (or some variation)
    2. Identify if either description is of the form "see department website" (or some variation)
    """
    desc1, desc2 = desc1.strip().lower(), desc2.strip().lower()
    # Case 1
    topics_vary_regex = re.compile("topics .{0,50} vary")
    # Case 2
    exclude_strings = [
        "department website for a current course description",
        "complete description of the current offerings",
        "department website for current description",
    ]
    for exclude_string in exclude_strings:
        if exclude_string in desc1 or exclude_string in desc2:
            return True

    for regex in [topics_vary_regex]:
        if re.match(regex, desc1) is not None or re.match(regex, desc2) is not None:
            return True

    return False


def split_into_sentences(text):
    # Adapted from https://stackoverflow.com/a/31505798
    alphabets = "([A-Za-z])"
    digits = "([0-9])"  # digits fix
    prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = r"(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov)"
    text = " " + text + "  "
    text = text.replace("\n", " ")
    text = re.sub(prefixes, "\\1<prd>", text)
    text = re.sub(websites, "<prd>\\1", text)
    text = re.sub(digits + "[.]" + digits, "\\1<prd>\\2", text)  # digits fix
    if "Ph.D" in text:
        text = text.replace("Ph.D.", "Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] ", " \\1<prd> ", text)
    text = re.sub(acronyms + " " + starters, "\\1<stop> \\2", text)
    text = re.sub(
        alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]", "\\1<prd>\\2<prd>\\3<prd>", text
    )
    text = re.sub(alphabets + "[.]" + alphabets + "[.]", "\\1<prd>\\2<prd>", text)
    text = re.sub(" " + suffixes + "[.] " + starters, " \\1<stop> \\2", text)
    text = re.sub(" " + suffixes + "[.]", " \\1<prd>", text)
    text = re.sub(" " + alphabets + "[.]", " \\1<prd>", text)
    if "”" in text:
        text = text.replace(".”", "”.")
    if '"' in text:
        text = text.replace('."', '".')
    if "!" in text:
        text = text.replace('!"', '"!')
    if "?" in text:
        text = text.replace('?"', '"?')
    text = text.replace(".", ".<stop>")
    text = text.replace("?", "?<stop>")
    text = text.replace("!", "!<stop>")
    text = text.replace("<prd>", ".")
    sentences = text.split("<stop>")
    sentences = [s.strip() for s in sentences]
    sentences = [s for s in sentences if s != ""]  # Drop empty (instead of dropping last)
    return sentences


def semantic_similarity(string_a, string_b):
    string_a = string_a.strip().lower()
    string_b = string_b.strip().lower()
    sentences_a = split_into_sentences(string_a)
    sentences_b = split_into_sentences(string_b)
    emb_a = (MODEL.encode(sentences_a, convert_to_tensor=True),)
    emb_b = MODEL.encode(sentences_b, convert_to_tensor=True)
    cosine_scores = util.cos_sim(emb_a, emb_b)
    nrows, ncols = cosine_scores.shape
    # compute traces divided by diagonal length
    # (only take diagonals that are of full length)
    max_trace = 0.0
    for offset in range(0, ncols - nrows + 1):  # [0, cols - rows]
        diag = np.diagonal(cosine_scores, offset=offset)
        max_trace = max(max_trace, np.sum(diag) / len(diag))
    return max_trace


def courses_similar(course_a, course_b):
    if lev_divided_by_avg_title_length(
        course_a.title, course_b.title
    ) > 0.8 and not title_special_case_heuristics(course_a.title, course_b.title):
        return True
    return (
        semantic_similarity(course_a.description, course_b.description) > 0.6
        and semantic_similarity(course_a.title, course_b.title) > 0.6
    )


def merge_topics(guaranteed_links=None, verbose=False):
    """
    Finds and merges Topics that should be merged.
    Args:
        guaranteed_links: Optionally, a `guaranteed_links` dict returned by
            `get_direct_backlinks_from_cross_walk`.
        verbose: If verbose=True, this script will print its progress and prompt for user input
            upon finding possible (but not definite) links. Otherwise it will run silently and
            log found possible links to Sentry (more appropriate if this function is called
            from an automated cron job like registrarimport).
    """
    if verbose:
        print("Merging topics...")
    guaranteed_links = guaranteed_links or dict()
    if verbose:
        print("Loading topics and courses from db (this may take a while)...")
    topics = set(Topic.objects.prefetch_related("courses", "courses__crosslistings").all())
    merge_count = 0

    iterator_wrapper = tqdm if verbose else lambda i: i
    for topic in iterator_wrapper(list(topics)):
        if topic not in topics:
            continue
        keep_linking = True
        while keep_linking:
            keep_linking = False
            for topic2 in topics:
                merged_courses = list(topic.courses) + list(topic2.courses)
                merged_courses.sort(key=lambda c: (c.semester, c.topic_id))
                course_links = []
                last = merged_courses[0]
                for course in merged_courses[1:]:
                    if last.topic_id != course.topic_id:
                        course_links.append((last, course))
                if any(
                    course_a.semester == course_b.semester
                    and not (
                        course_a.full_code == course_b.full_code
                        or any(
                            course_ac.full_code == course_b.full_code
                            for course_ac in course_a.crosslistings
                        )
                    )
                    for course_a, course_b in course_links
                ):
                    continue
                if (
                    should_link_courses(last, course, verbose=verbose)
                    != ShouldLinkCoursesResponse.DEFINITELY
                ):
                    continue
                topics.remove(topic)
                topics.remove(topic2)
                topic = topic.merge_with(topic2)
                topics.add(topic)
                merge_count += 1
                keep_linking = True
                break

    if verbose:
        print(f"Done merging topics (performed {merge_count} merges).")
