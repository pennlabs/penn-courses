import logging
import os
import re
from collections import defaultdict
from enum import Enum, auto
from itertools import zip_longest
from textwrap import dedent

import jellyfish
import numpy as np
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm

from courses.models import Topic
from PennCourses.settings.base import S3_client


def get_branches_from_cross_walk(cross_walk):
    """
    From a given crosswalk csv path, generate a dict mapping old_full_code to
    a list of the new codes originating from that source, if there are multiple
    (i.e. only in the case of branches).
    """
    branched_links = defaultdict(list)
    cross_walk = pd.read_csv(cross_walk, delimiter="|", encoding="unicode_escape")
    for _, r in cross_walk.iterrows():
        old_full_code = f"{r['SRS_SUBJ_CODE']}-{r['SRS_COURSE_NUMBER']}"
        new_full_code = f"{r['NGSS_SUBJECT']}-{r['NGSS_COURSE_NUMBER']}"
        branched_links[old_full_code].append(new_full_code)
    return {
        old_code: new_codes for old_code, new_codes in branched_links.items() if len(new_codes) > 1
    }


MODEL = SentenceTransformer("all-MiniLM-L6-v2")


def get_direct_backlinks_from_cross_walk(cross_walk):
    """
    From a given crosswalk csv path, generate a dict mapping new_full_code->old_full_code,
    ignoring branched links in the crosswalk (a course splitting into multiple new courses).
    """
    links = defaultdict(list)
    cross_walk = pd.read_csv(cross_walk, delimiter="|", encoding="unicode_escape")
    for _, r in cross_walk.iterrows():
        old_full_code = f"{r['SRS_SUBJ_CODE']}-{r['SRS_COURSE_NUMBER']}"
        new_full_code = f"{r['NGSS_SUBJECT']}-{r['NGSS_COURSE_NUMBER']}"
        links[old_full_code].append(new_full_code)
    return {old_code: new_codes[0] for old_code, new_codes in links.items() if len(new_codes) == 1}


def prompt_for_link_multiple(courses, extra_newlines=True):
    """
    Prompts the user to confirm or reject a possible link between multiple courses.
    Returns a boolean representing whether the courses should be linked.
    """
    print("\n\n============>\n")
    print("\n".join(course.full_str() for course in courses))
    print("\n<============")
    prompt = input(f"Should the above {len(courses)} courses be linked? (y/N) ")
    if extra_newlines:
        print("\n\n")
    return prompt.strip().upper() == "Y"


def prompt_for_link(course1, course2):
    """
    Prompts the user to confirm or reject a possible link between courses.
    Returns a boolean representing whether the courses should be linked.
    """
    return prompt_for_link_multiple([course1, course2])


def same_course(course_a, course_b):
    return course_a.full_code == course_b.full_code or any(
        course_ac.full_code == course_b.full_code
        for course_ac in (course_a.primary_listing or course_a).listing_set.all()
    )


class ShouldLinkCoursesResponse(Enum):
    DEFINITELY = auto()
    MAYBE = auto()
    NO = auto()


def should_link_courses(course_a, course_b, verbose=True):
    """
    Checks if the two courses should be linked, based on information about those
    courses stored in our database. Prompts for user input in the case of possible links,
    if in verbose mode (otherwise just logs possible links).
    Returns a response in the form of a ShouldLinkCoursesResponse enum.
    """
    if same_course(course_a, course_b):
        return ShouldLinkCoursesResponse.DEFINITELY
    elif course_a.semester == course_b.semester:
        return ShouldLinkCoursesResponse.NO
    elif (course_a.code < "5000") != (course_b.code < "5000"):
        return ShouldLinkCoursesResponse.NO
    elif courses_similar(course_a, course_b):  # TODO
        # If title is same or (title is similar and description is similar
        # have a fairly low threshold for similarity)
        # TODO: search for "topics vary" in description, say no
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
    starters = r"(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|" \
               r"Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov)"
    text = " " + text + "  "
    text = text.replace("\n", " ")
    text = re.sub(prefixes, "\\1<prd>", text)
    text = re.sub(websites, "<prd>\\1", text)
    text = re.sub(digits + "[.]" + digits, "\\1<prd>\\2", text)  # digits fix
    if "Ph.D" in text:
        text = text.replace("Ph.D.", "Ph<prd>D<prd>")
    text = re.sub(r"\s" + alphabets + "[.] ", " \\1<prd> ", text)
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
        print("Merging topics")
    guaranteed_links = guaranteed_links or dict()
    if verbose:
        print("Loading topics and courses from db (this may take a while)...")
    topics = set(
        Topic.objects.prefetch_related(
            "courses",
            "courses__listing_set",
            "courses__primary_listing",
            "courses__primary_listing__listing_set",
        ).all()
    )
    dont_link = set()
    merge_count = 0

    for topic in tqdm(list(topics), disable=(not verbose)):
        if topic not in topics:
            continue
        keep_linking = True
        while keep_linking:
            keep_linking = False
            for topic2 in topics:
                if topic == topic2:
                    continue
                merged_courses = list(topic.courses.all()) + list(topic2.courses.all())
                merged_courses.sort(key=lambda c: (c.semester, c.topic_id))
                course_links = []
                last = merged_courses[0]
                for course in merged_courses[1:]:
                    if last.topic_id != course.topic_id:
                        course_links.append((last, course))
                    last = course
                if any(
                    course_a.semester == course_b.semester and not same_course(course_a, course_b)
                    for course_a, course_b in course_links
                ):
                    continue
                should_link = True
                for last, course in course_links:
                    if (last, course) in dont_link or (
                        should_link_courses(last, course, verbose=verbose)
                        != ShouldLinkCoursesResponse.DEFINITELY
                    ):
                        dont_link.add((last, course))
                        should_link = False
                        break
                if should_link:
                    topics.remove(topic)
                    topics.remove(topic2)
                    topic = topic.merge_with(topic2)
                    topics.add(topic)
                    merge_count += 1
                    keep_linking = True
                    break

    if verbose:
        print(f"Finished merging topics (performed {merge_count} merges).")


def manual_merge(topic_ids):
    invalid_ids = [i for i in topic_ids if not i.isdigit()]
    if invalid_ids:
        print(
            f"The following topic IDs are invalid (non-integer):\n{invalid_ids}\n" "Aborting merge."
        )
        return
    topic_ids = [int(i) for i in topic_ids]
    topics = Topic.objects.filter(id__in=topic_ids).prefetch_related("courses")
    found_ids = topics.values_list("id", flat=True)
    not_found_ids = list(set(topic_ids) - set(found_ids))
    if not_found_ids:
        print(f"The following topic IDs were not found:\n{not_found_ids}\nAborting merge.")
        return
    courses = [course for topic in topics for course in topic.courses.all()]
    if not prompt_for_link_multiple(courses, extra_newlines=False):
        print("Aborting merge.")
        return
    with transaction.atomic():
        topic = topics[0]
        for topic2 in topics[1:]:
            topic = topic.merge_with(topic2)
    print(f"Successfully merged {len(topics)} topics into: {topic}.")


class Command(BaseCommand):
    help = (
        "This script uses a combination of an optionally provided crosswalk, heuristics, "
        "and user input to merge Topics in the database."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--cross-walk",
            type=str,
            help=dedent(
                """
                Optionally specify a path to a crosswalk specifying links between course codes
                (in the format provided by Susan Collins [squant@isc.upenn.edu] from
                the data warehouse team; https://bit.ly/3HtqPq3).
                """
            ),
            default="",
        )
        parser.add_argument(
            "-s3", "--s3_bucket", help="download crosswalk from specified s3 bucket."
        )
        parser.add_argument(
            "-t",
            "--topic_ids",
            nargs="*",
            help=dedent(
                """
            Optionally, specify a (space-separated) list of Topic IDs to merge into a single topic.
            You can find Topic IDs from the django admin interface (either by searching through
            Topics or by following the topic field from a course entry).
            If this argument is omitted, the script will automatically detect merge opportunities
            among all Topics, prompting the user for confirmation before merging in each case.
            """
            ),
            required=False,
        )

    def handle(self, *args, **kwargs):
        cross_walk_src = kwargs["cross_walk"]
        s3_bucket = kwargs["s3_bucket"]
        topic_ids = set(kwargs["topic_ids"])

        print(
            "This script is atomic, meaning either all Topic merges will be comitted to the "
            "database, or otherwise if an error is encountered, all changes will be rolled back "
            "and the database will remain as it was before the script was run."
        )

        if topic_ids:
            manual_merge(topic_ids)
            return

        if cross_walk_src and s3_bucket:
            fp = "/tmp/" + cross_walk_src
            print(f"downloading crosswalk from s3://{s3_bucket}/{cross_walk_src}")
            S3_client.download_file(s3_bucket, cross_walk_src, fp)
            cross_walk_src = fp

        guaranteed_links = (
            get_direct_backlinks_from_cross_walk(cross_walk_src) if cross_walk_src else dict()
        )

        if cross_walk_src and s3_bucket:
            # Remove temporary file
            os.remove(cross_walk_src)

        with transaction.atomic():
            merge_topics(guaranteed_links=guaranteed_links, verbose=True)
