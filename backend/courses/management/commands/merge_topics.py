import logging
from enum import Enum, auto

from tqdm import tqdm

from courses.models import Topic

import re
from itertools import zip_longest

import jellyfish

import numpy as np
import torch
from tqdm.autonotebook import trange

class ShouldLinkCoursesResponse(Enum):
    DEFINITELY = auto()
    MAYBE = auto()
    NO = auto()


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
    else:
         # If the title is effectively the same, and does not fall into a heuristic case
         similar_title = (lev_divided_by_avg_title_length(course_a.title, course_b.title) > .8 and
                          not title_special_case_heuristics(course_a.title, course_b.title))

         # If both the title and description are very similar semantically (as best as can be told)
         semantically_similar_title_description = (
                 semantic_similarity(course_a.description, course_b.description) > .8 and semantic_similarity(course_a.title, course_b.title) > .8
         )

        if similar_title or semantically_similar_title_description:
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
    1. Identify if a course title is different only by a single roman numeral or digit:
       ie CIS-120 is "Programming Languages and Techniques I" and CIS-121 is
       "Programming Languages and Techniques II". The specific means of doing this is to check if the segment
       directly preceding a roman numeral or number is identical. If it is then the title falls into this case.
    """
    title1, title2 = title1.strip(), title2.strip()
    # Case 1
    sequels_regex = re.compile("(\d|IX|IV|V?I{0,3})")
    splits = zip_longest(re.split(sequels_regex, title1), re.split(sequels_regex, title2))
    previous_split = None
    for i, split1, split2 in enumerate(splits):
        if i % 2 == 0:
            previous_split = split1 == split2
        else:
            if split1 != split2 and previous_split:
                return False
    return True

def description_special_case_heuristics(desc1, desc2):
    """
    Handle special cases (specifically when the description is non-informative because it does not
    contain course-specific content) and return True if they occur, False otherwise.
    1. Identify if either description is of the form "topics may vary" (or some variation)
    2. Identify if either description is of the form "see department website" (or some variation
    """
    desc1, desc2 = desc1.strip().lower(), desc2.strip().lower()
    # Case 1
    topics_vary_regex = re.compile("topics .{0,50} vary")

    # Case 2
    # TODO: turn into regex?
    exclude_strings = ["department website for a current course description",
                       "complete description of the current offerings",
                       "department website for current description"]
    for exclude_string in exclude_strings:
        if exclude_string in desc1 or exclude_string in desc2:
            return True

    for regex in [topics_vary_regex]:
        if (re.match(regex, desc1) is not None or
            re.match(regex, desc2) is not None):
            return True

    return False

def semantic_similarity(string_a, string_b):
    return 1.0

def get_embbedding(sentences,
                   normalize_embeddings = False,
                   batch_size=32,
                   show_progress_bar=True
                   ):
    # Adapted from
    # https://github.com/UKPLab/sentence-transformers/blob/master/sentence_transformers/SentenceTransformer.py


    # Sentences sorted by length hi-to-lo
    length_sorted_idx = np.argsort([-len(sen) for sen in sentences])
    sentences_sorted = [sentences[idx] for idx in length_sorted_idx]
    all_embeddings = []
    for start_index in trange(0, len(sentences), batch_size, desc="Batches", disable=not show_progress_bar):
        sentences_batch = sentences_sorted[start_index:start_index+batch_size]
        # Tokenize
        features = self.tokenize(sentence_batch)

        with torch.no_grad():
            out_features = self.forward(features)
            embeddings = out_features["sentence_embedding"] # output_value = "sentence_embeddings"
            embeddings = embeddings.detach()
            if normalize_embeddings:
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

        all_embeddings.extend(embeddings)

    # Normalize (based on arg)
    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

    # Return sorted by lenth lo-to-hi
    all_embeddings = [all_embeddings[idx] for idx in np.argsort(length_sorted_idx)]

    return all_embeddings

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
