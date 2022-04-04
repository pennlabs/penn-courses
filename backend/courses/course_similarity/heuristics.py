import re

import nltk
import numpy as np
from jellyfish import levenshtein_distance
from sentence_transformers import SentenceTransformer, util

from courses.util import in_dev


if in_dev():
    nltk.download("punkt")
SENT_TOKENIZER = nltk.data.load("nltk:tokenizers/punkt/english.pickle")
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def title_rejection_heuristics(title_a, title_b):
    """
    Handle special cases indicating dissimilarity and return True if they occur, False otherwise.
    0.  At least one string is only whitespace
    1.  The title equals "dissertation"
    2.  Identify if a course title is different only by a single roman numeral or digit:
        ie CIS-120 is "Programming Languages and Techniques I" and CIS-121 is
        "Programming Languages and Techniques II". The specific means of doing
        this is to check if the segment directly preceding a roman numeral or
        number is identical. If it is then the title falls into this case.
    3.  Identify if a course differs by "beginner, intermediate, or advanced" at
        the start of the title (or synonyms for each respective word). Note
        additional levels like "Advanced intermediate" only have their first
        word (e.g., "Advanced") considered. Note also that if one title doesn't
        have such a first word, but the other does, False is returned.
    """
    # Case 0
    if title_a == "" or title_b == "":
        return True

    # Case 1
    if title_a == "dissertation" or title_b == "dissertation":
        return True

    # Case 2
    sequels_regex = re.compile(r"\s+(\d+|ix|iv|v?i{0,3})$")
    match_a, match_b = sequels_regex.search(title_a), sequels_regex.search(title_b)
    if (match_a is not None) != (match_b is not None):
        return True
    if match_a and match_b and match_a.group(1) != match_b.group(1):
        return True

    # Case 3
    levels = {
        "introductory": 0,
        "intruduction": 0,
        "beginner": 0,
        "elementary": 0,
        "intermediate": 1,
        "advanced": 2,
    }

    def get_level(title):
        level = -1
        for keyword, lev in levels.items():
            if keyword in title:
                level = lev
        return level

    if get_level(title_a) != get_level(title_b):
        return True

    return False


def description_rejection_heuristics(desc_a, desc_b):
    """
    Handle special cases (specifically when the description is non-informative because it does not
    contain course-specific content) and return True if they occur, False otherwise.
    0. At least one string is only whitespace
    1. Identify if either description is of the form "topics may vary" (or some variation)
    2. Identify if either description is of the form "see department website" (or some variation)
    """
    # Case 0
    if desc_a == "" or desc_b == "":
        return True

    # Case 1
    topics_vary_regex = re.compile(r"topics\s*.*vary")

    # Case 2
    exclude_strings = [
        "department website for a current course description",
        "complete description of the current offerings",
        "department website for current description",
    ]
    for exclude_string in exclude_strings:
        if exclude_string in desc_a or exclude_string in desc_b:
            return True
    for regex in [topics_vary_regex]:
        if regex.search(desc_a) or regex.search(desc_b):
            return True

    return False


def lev_divided_by_avg_length(a, b):
    """
    Compute levenshtein distance between 2 strings and then divide by avg length.
    """
    return 2 * levenshtein_distance(a, b) / (len(a) + len(b))


def semantic_similarity(string_a, string_b):
    """
    Compute the semantics similarity between two strings. The strings are split
    into sentences, then those sentences are turned into embeddings, and then
    cosine similarity between matching sentences is computed. If the two strings
    have different numbers of sentences, take the maximum similarity matching that
    contains as many sentences as possible. Assumes both strings are not just
    whitespace.
    """
    sentences_a = SENT_TOKENIZER.tokenize(string_a)
    sentences_b = SENT_TOKENIZER.tokenize(string_b)
    emb_a = embedder.encode(sentences_a, convert_to_tensor=True)
    emb_b = embedder.encode(sentences_b, convert_to_tensor=True)
    cosine_scores = util.cos_sim(emb_a, emb_b)
    nrows, ncols = cosine_scores.shape
    # compute tr/len(diag) for maximal length diagonals
    max_trace = 0.0
    for offset in range(0, ncols - nrows + 1):  # [0, cols - rows]
        diag = np.diagonal(cosine_scores, offset=offset)
        max_trace = max(max_trace, np.sum(diag) / len(diag))
    return max_trace
