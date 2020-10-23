import re
from typing import Dict, List


def titleize(name):
    """
    Titleize a course name or instructor, taking into account exceptions such as II.
    """
    # string.title() will capitalize the first letter of every word,
    # where a word is a substring delimited by a non-letter character. So, "o'leary" is two words
    # and will be capitalized (properly) as "O'Leary".
    name = name.strip().title()
    # Roman-numeral suffixes
    name = re.sub(r"([XVI])(x|v|i+)", lambda m: m.group(1) + m.group(2).upper(), name)
    # "1st".title() -> "1St", but it should still be "1st".
    name = re.sub(r"(\d)(St|Nd|Rd|Th)", lambda m: m.group(1) + m.group(2).lower(), name)
    # Like McDonald.
    name = re.sub(r"Mc([a-z])", lambda m: "Mc" + m.group(1).upper(), name)
    # Possessives shouldn't get capitalized.
    name = name.replace("'S", "'s")
    return name


def to_r_camel(s):
    """
    Turns fields from python snake_case to the PCR frontend's rCamelCase.
    """
    return "r" + "".join([x.title() for x in s.split("_")])


def make_subdict(field_prefix, d):
    """
    Rows in a queryset that don't represent related database models are flat. But we want
    our JSON to have a nested structure that makes more sense to the client. This function
    takes fields from a flat dictionary with a certain prefix and returns a dictionary
    of those entries, with the prefix removed from the keys.
    """
    start_at = len(field_prefix)
    return {
        to_r_camel(k[start_at:]): v
        for k, v in d.items()
        if k.startswith(field_prefix) and v is not None
    }


def dict_average(entries: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Average a list of dicts into one dict with averages.
    :param entries:
    :return:
    """
    keys = set()
    for entry in entries:
        keys.update(entry.keys())

    averages = {k: (0, 0) for k in keys}
    for entry in entries:
        for k, v in entry.items():
            sum_, count_ = averages[k]
            averages[k] = (sum_ + v, count_ + 1)

    return {k: v[0] / v[1] if v[1] > 0 else 0 for k, v in averages.items()}


def aggregate_reviews(reviews, group_by, **extra_fields):
    """
    Aggregate a list of reviews, grouping by some field.
    :param reviews: A list of dictionaries representing Review objects, with reviewbits inlined
    using review.annotations.review_averages(). And dict-ified by calling .values() on a queryset.
    :param group_by: Field to group by in the review.
    :param extra_fields: Any extra fields from the dictionaries to carry through to the response.
    :return: Average reviews, recent reviews, number of semesters taught, and other data needed
    for the response to the frontend.
    """
    grouped_reviews = dict()
    # First pass: Group individual reviews by the provided key.
    for review in reviews:
        key = review[group_by]
        grouped_reviews.setdefault(key, []).append(
            {
                "semester": review["semester"],
                "scores": make_subdict("bit_", review),
                **{
                    response_prop: review[instance_prop]
                    for response_prop, instance_prop in extra_fields.items()
                },
            }
        )
    aggregated = dict()
    # Second pass: Aggregate grouped reviews by taking the average of all scores and recent scores.
    for k, reviews in grouped_reviews.items():
        latest_sem = max([r["semester"] for r in reviews])
        all_scores = [r["scores"] for r in reviews]
        recent_scores = [r["scores"] for r in reviews if r["semester"] == latest_sem]
        aggregated[k] = {
            "id": k,
            "average_reviews": dict_average(all_scores),
            "recent_reviews": dict_average(recent_scores),
            "latest_semester": latest_sem,
            "num_semesters": len(set([r["semester"] for r in reviews])),
            **{extra_field: reviews[0][extra_field] for extra_field, _ in extra_fields.items()},
        }

    return aggregated
