import re
from typing import Dict, List

import numpy as np
from django.db.models import F


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

    return {k: round(v[0] / v[1], 2) if v[1] > 0 else 0 for k, v in averages.items()}


def aggregate_reviews(reviews, group_by, **extra_fields):
    """
    Aggregate a list of reviews (as dictionaries), grouping by some field.
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


def average_given_plots(plots_dict):
    """
    Given plots (i.e. demands plots or section status plots), which should be a dict with
    plot lists as leaves at some depth, aggregate all these plots and return a single average plot.
    For instance, if a dict mapping semesters to section ids to demand plot lists is given,
    this function will return the average demand plot across all given sections and semesters.
    If a dict mapping section ids to section status plot lists is given,
    this function will return a plot of the average percentage of the given sections that
    were open at each point in time.
    Returns None if no valid plots are found in the given plots_dict dict.
    Note that demand plots are lists of tuples of the form (percent_through, value).
    """
    # Extract plots from dict
    plots = []  # A list of all plots in the dict

    def explore(to_explore):
        if isinstance(to_explore, dict):
            for value in to_explore.values():
                explore(value)
        elif isinstance(to_explore, list):
            plots.append(to_explore)

    explore(plots_dict)

    if len(plots) == 0:
        return None

    assert all(len(plot) > 0 for plot in plots), f"Empty plot given: \n{plots}"
    demand_frontier = [plots[i][0] for i in range(len(plots))]
    # demand_frontier: A list mapping plots index to the most recently considered demand update
    # from that plot in the averaged plot
    assert all(
        el[0] == 0 for el in demand_frontier
    ), f"Some plots in the given plots_dict dict do not start at 0: \n{plots}"
    frontier_candidate_indices = [1 for _ in range(len(plots))]
    # frontier_candidate_indices: A list of the indices of the next candidate elements to add to
    # the frontier

    def get_average():
        return sum([tup[1] for tup in demand_frontier]) / len(demand_frontier)

    averaged_plot = [(0, get_average())]
    # averaged_plot: This will be our final averaged plot (which we will return)
    while any(plot_idx < len(plots[i]) for i, plot_idx in enumerate(frontier_candidate_indices)):
        min_percent_through = min(
            plots[i][frontier_candidate_indices[i]][0]
            for i in range(len(plots))
            if frontier_candidate_indices[i] < len(plots[i])
        )
        for i in range(len(plots)):
            if (
                frontier_candidate_indices[i] < len(plots[i])
                and abs(plots[i][frontier_candidate_indices[i]][0] - min_percent_through) < 0.000001
            ):
                demand_frontier[i] = plots[i][frontier_candidate_indices[i]]
                frontier_candidate_indices[i] += 1
        averaged_plot.append((min_percent_through, get_average()))
    return averaged_plot


def avg_and_recent_demand_plots(section_map, num_points=100):
    """
    Aggregate demand plots over time (during historical add/drop periods) for the given
    sections (specified by section_map).
    Demand plots are lists of tuples of the form (percent_through, relative_demand).
    The average plot will average across all sections, and the recent plot will average across
    sections from only the most recent semester.
    Note that section_map should map semester to section id to section object.
    The generated plots will have points at increments of step_size in the range [0,1].
    Returns (avg_demand_plot, recent_demand_plot)
    """
    from alert.models import AddDropPeriod, PcaDemandExtrema, Registration

    # ^ imported here to avoid circular imports
    add_drop_periods = AddDropPeriod.objects.filter(semester__in=section_map.keys())
    add_drop_periods_map = dict()
    # add_drop_periods_map: maps semester to that semester's add drop period object
    for adp in add_drop_periods:
        add_drop_periods_map[adp.semester] = adp
    demand_extrema = PcaDemandExtrema.objects.filter(
        semester__in=section_map.keys(), in_add_drop_period=True
    ).select_related("most_popular_section", "least_popular_section")
    demand_extrema_map = dict()
    # demand_extrema_map: maps semester to a list of the demand extrema from that semester
    for ext in demand_extrema:
        if ext.semester not in demand_extrema_map:
            demand_extrema_map[ext.semester] = []
        demand_extrema_map[ext.semester].append(ext)
    registrations_map = dict()
    # registrations_map: maps semester to section id to a list of registrations from that section
    for semester in section_map.keys():
        registrations_map[semester] = dict()
        for section_id in section_map[semester].keys():
            registrations_map[semester][section_id] = []
    section_id_to_semester = {
        section_id: semester
        for semester in section_map.keys()
        for section_id in section_map[semester].keys()
    }
    registrations = Registration.objects.filter(section_id__in=section_id_to_semester.keys())
    for registration in registrations:
        semester = section_id_to_semester[registration.section_id]
        registrations_map[semester][registration.section_id].append(registration)

    demand_plots_map = dict()
    # demand_plots_map: maps semester to section id to the demand plot of that section

    # Now that all database work has been completed, let's iterate through
    # our semesters and compute demand plots for each section
    for semester in section_map.keys():
        demand_plots_map[semester] = dict()
        add_drop_period = add_drop_periods_map[semester]
        if semester not in demand_extrema_map:
            continue
        demand_extrema_changes = [
            {
                "percent_through": ext.percent_through_add_drop_period,
                "type": "extrema_change",
                "lowest": ext.lowest_raw_demand,
                "highest": ext.highest_raw_demand,
            }
            for ext in demand_extrema_map[semester]
        ]
        if len(demand_extrema_changes) == 0:
            continue
        for i, section in enumerate(section_map[semester].values()):
            section_id = section.id
            capacity = section.capacity
            if capacity is None or capacity <= 0:
                continue
            volume_changes = []
            # volume_changes: a list containing registration volume changes over time
            for registration in registrations_map[semester][section_id]:
                volume_changes.append(
                    {
                        "percent_through": add_drop_period.get_percent_through_add_drop(
                            registration.created_at
                        ),
                        "volume_change": 1,
                        "type": "volume_change",
                    }
                )
                deactivated_at = registration.deactivated_at
                if deactivated_at is not None:
                    volume_changes.append(
                        {
                            "percent_through": add_drop_period.get_percent_through_add_drop(
                                deactivated_at
                            ),
                            "volume_change": -1,
                            "type": "volume_change",
                        }
                    )
            demand_plot = [(0, 0)]
            # demand_plot: the demand plot for this section, containing elements of the form
            # (percent_through, relative_demand)
            changes = sorted(
                volume_changes + demand_extrema_changes, key=lambda x: x["percent_through"]
            )
            registration_volume = 0
            latest_raw_demand_extrema = None

            changes_idx = 0
            for x in np.linspace(0, 1, num=num_points + 1)[1:]:  # skip 0
                total_value_in_bin = 0
                num_in_bin = 0
                while changes_idx < len(changes) and changes[changes_idx]["percent_through"] <= x:
                    change = changes[changes_idx]
                    changes_idx += 1
                    if change["type"] == "extrema_change":
                        latest_raw_demand_extrema = change
                    else:
                        if latest_raw_demand_extrema is None:
                            continue
                        registration_volume += change["volume_change"]
                    min_val = float(latest_raw_demand_extrema["lowest"])
                    max_val = float(latest_raw_demand_extrema["highest"])
                    if min_val == max_val:
                        rel_demand = 0.5
                    else:
                        rel_demand = float(registration_volume / capacity - min_val) / float(
                            max_val - min_val
                        )
                    total_value_in_bin += rel_demand
                    num_in_bin += 1
                demand_plot.append(
                    (x, total_value_in_bin / num_in_bin if num_in_bin > 0 else demand_plot[-1][1])
                )

            demand_plots_map[semester][section_id] = demand_plot

    recent_demand_plot = average_given_plots(demand_plots_map[max(section_map.keys())])
    avg_demand_plot = average_given_plots(demand_plots_map)
    return avg_demand_plot, recent_demand_plot


def avg_and_recent_percent_open_plots(section_map, num_points=100):
    """
    Aggregate plots of the percentage of sections that were open at each point in time (during
    historical add/drop periods) for the given sections (specified by section_map).
    Percentage-open plots are lists of tuples of the form (percent_through, percentage_open).
    The average plot will average across all sections, and the recent plot will average across
    sections from only the most recent semester.
    Note that section_map should map semester to section id to section object.
    The generated plots will have points at increments of step_size in the range [0,1].
    Returns (avg_percent_open_plot, recent_percent_open_plot)
    """
    from courses.models import StatusUpdate  # imported here to avoid circular imports

    section_id_to_semester = {
        section.id: section.efficient_semester
        for semester in section_map.keys()
        for section in section_map[semester].values()
    }
    status_updates = StatusUpdate.objects.filter(
        section_id__in=section_id_to_semester.keys(), in_add_drop_period=True
    ).annotate(semester=F("section__course__semester"))
    status_updates_map = dict()
    # status_updates_map: maps semester to section id to the status updates for that section
    for semester in section_map.keys():
        status_updates_map[semester] = dict()
        for section_id in section_map[semester].keys():
            status_updates_map[semester][section_id] = []
    for status_update in status_updates:
        status_updates_map[status_update.semester][status_update.section_id].append(status_update)

    open_plots = dict()
    # open_plots: maps semester to section id to the plot of when that section was open during
    # the add/drop period (1 if open, 0 if not)

    # Now that all database work has been completed, let's iterate through
    # our semesters and compute open plots for each section
    for semester in section_map.keys():
        open_plots[semester] = dict()
        for section in section_map[semester].values():
            section_id = section.id
            updates = sorted(
                status_updates_map[semester][section_id],
                key=lambda x: x.percent_through_add_drop_period,
            )
            if len(updates) == 0:
                estimate_open = int(section.percent_open > 0.5)
                open_plots[semester][section_id] = [(0, estimate_open), (1, estimate_open)]
                continue
            open_plot = [(0, int(updates[0].old_status == "O"))]
            # open_plot: the demand plot for this section, containing elements of the form
            # (percent_through, relative_demand).

            latest_status = int(updates[0].old_status == "O")
            updates_idx = 0
            for x in np.linspace(0, 1, num=num_points + 1)[1:]:  # skip 0
                while (
                    updates_idx < len(updates)
                    and updates[updates_idx].percent_through_add_drop_period <= x
                ):
                    update = updates[updates_idx]
                    updates_idx += 1
                    if int(update.old_status == "O") != latest_status:
                        # Ignore invalid status updates
                        continue
                    latest_status = int(update.new_status == "O")
                open_plot.append((x, latest_status))

            open_plots[semester][section_id] = open_plot

    recent_percent_open_plot = average_given_plots(open_plots[max(section_map.keys())])
    avg_percent_open_plot = average_given_plots(open_plots)
    return avg_percent_open_plot, recent_percent_open_plot
