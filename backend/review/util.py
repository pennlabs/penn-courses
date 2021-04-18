import re
from typing import Dict, List

import scipy.stats as stats
from django.db.models import F
from tqdm import tqdm

from PennCourses.settings.base import (
    PCA_REGISTRATIONS_RECORDED_SINCE,
    STATUS_UPDATES_RECORDED_SINCE,
)


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


def average_given_plots(plots_dict, bin_size=0.000001):
    """
    Given plots (i.e. demands plots or section status plots), which should be a dict with
    plot lists as leaves at some depth, aggregate all these plots and return a single average plot.
    For instance, if a dict mapping semesters to section ids to demand plot lists is given,
    this function will return the average demand plot across all given sections and semesters.
    If a dict mapping section ids to section status plot lists is given,
    this function will return a plot of the average percentage of the given sections that
    were open at each point in time.
    The bin_size argument allows you to specify how far after a certain data point to squash
    following data points and average into the same point. By default, only data points
    that are within 0.000001 will be squashed (i.e. almost equal, ignoring floating point
    precision issues).
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
    frontier_candidate_indices = [0 for _ in range(len(plots))]
    # frontier_candidate_indices: A list of the indices of the next candidate elements to add to
    # the frontier

    averaged_plot = []
    latest_values = [None for _ in range(len(plots))]
    # averaged_plot: This will be our final averaged plot (which we will return)
    while any([plot_idx < len(plots[i]) for i, plot_idx in enumerate(frontier_candidate_indices)]):
        min_percent_through = min(
            plots[i][frontier_candidate_indices[i]][0]
            for i in range(len(plots))
            if frontier_candidate_indices[i] < len(plots[i])
        )
        plots_bins = [[] for _ in range(len(plots))]
        # plots_bins is a list of lists of y values (one list for each given plot)
        for plot_num in range(len(plots)):
            new_frontier_candidate_index = frontier_candidate_indices[plot_num]
            take_latest_value = True
            while (
                new_frontier_candidate_index < len(plots[plot_num])
                and plots[plot_num][new_frontier_candidate_index][0]
                <= min_percent_through + bin_size
            ):
                take_latest_value = False
                plots_bins[plot_num].append(plots[plot_num][new_frontier_candidate_index][1])
                new_frontier_candidate_index += 1
            if take_latest_value and latest_values[plot_num] is not None:
                plots_bins[plot_num].append(latest_values[plot_num])
            frontier_candidate_indices[plot_num] = new_frontier_candidate_index
        latest_values = [sum(lst) / len(lst) if len(lst) > 0 else None for lst in plots_bins]
        non_null_latest_values = [val for val in latest_values if val is not None]
        averaged_plot.append(
            (min_percent_through, sum(non_null_latest_values) / len(non_null_latest_values))
        )
    return averaged_plot


def get_status_updates_map(section_map):
    """
    Returns status_updates_map, mapping semester to section id to a list of status updates
    for that section. Every section from the given section_map dict is represented in the
    returned status_updates_map dict. Note that section_map should map semester to section id
    to section object.
    """
    from courses.models import StatusUpdate  # imported here to avoid circular imports

    status_updates = StatusUpdate.objects.filter(
        section_id__in=[
            section_id for semester in section_map.keys() for section_id in section_map[semester]
        ],
        in_add_drop_period=True,
    ).annotate(semester=F("section__course__semester"))
    status_updates_map = dict()
    # status_updates_map: maps semester to section id to the status updates for that section
    for semester in section_map.keys():
        status_updates_map[semester] = dict()
        for section_id in section_map[semester].keys():
            status_updates_map[semester][section_id] = []
    for status_update in status_updates:
        status_updates_map[status_update.semester][status_update.section_id].append(status_update)
    return status_updates_map


def avg_and_recent_demand_plots(section_map, status_updates_map, bin_size=0.01):
    """
    Aggregate demand plots over time (during historical add/drop periods) for the given
    sections (specified by section_map).
    Demand plots are lists of tuples of the form (percent_through, relative_demand).
    The average plot will average across all sections, and the recent plot will average across
    sections from only the most recent semester.
    Note that section_map should map semester to section id to section object.
    The status_updates_map should map semester to section id to a list of status updates
    for that section (this can be retrieved with the call get_status_updates_map(section_map)).
    Points are grouped together with all all remaining points within bin_size to the right,
    so the minimum separation between data points will be bin_size.
    Returns (avg_demand_plot, avg_demand_plot_min_semester, avg_percent_open_plot_num_semesters,
             recent_demand_plot, recent_demand_plot_semester)
    """
    from alert.models import AddDropPeriod, PcaDemandDistributionEstimate, Registration

    # ^ imported here to avoid circular imports
    add_drop_periods = AddDropPeriod.objects.filter(semester__in=section_map.keys())
    add_drop_periods_map = dict()
    # add_drop_periods_map: maps semester to that semester's add drop period object
    for adp in add_drop_periods:
        add_drop_periods_map[adp.semester] = adp
    demand_distribution_estimates = PcaDemandDistributionEstimate.objects.filter(
        semester__in=section_map.keys(), in_add_drop_period=True
    ).select_related("highest_demand_section", "lowest_demand_section")
    demand_distribution_estimates_map = dict()
    # demand_distribution_estimates_map: maps semester
    # to a list of the demand distribution_estimates from that semester
    for ext in demand_distribution_estimates:
        if ext.semester not in demand_distribution_estimates_map:
            demand_distribution_estimates_map[ext.semester] = []
        demand_distribution_estimates_map[ext.semester].append(ext)
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
        if semester < PCA_REGISTRATIONS_RECORDED_SINCE:
            continue
        demand_plots_map[semester] = dict()
        add_drop_period = add_drop_periods_map[semester]
        if semester not in demand_distribution_estimates_map:
            continue
        demand_distribution_estimates_changes = [
            {
                "percent_through": ext.percent_through_add_drop_period,
                "type": "distribution_estimate_change",
                "csdv_gamma_param_alpha": ext.csdv_gamma_param_alpha,
                "csdv_gamma_param_loc": ext.csdv_gamma_param_loc,
                "csdv_gamma_param_scale": ext.csdv_gamma_param_scale,
                "mean_log_likelihood": ext.csdv_gamma_fit_mean_log_likelihood
            }
            for ext in demand_distribution_estimates_map[semester]
        ]
        if len(demand_distribution_estimates_changes) == 0:
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
            status_updates_list = [
                {
                    "percent_through": update.percent_through_add_drop_period,
                    "type": "status_update",
                    "old_status": update.old_status,
                    "new_status": update.new_status,
                }
                for update in status_updates_map[semester][section_id]
            ]
            demand_plot = [(0, 0)]
            # demand_plot: the demand plot for this section, containing elements of the form
            # (percent_through, relative_demand)
            changes = sorted(
                volume_changes + demand_distribution_estimates_changes + status_updates_list,
                key=lambda x: x["percent_through"],
            )

            # Initialize variables to be maintained in our main changes loop
            registration_volume = 0
            latest_raw_demand_distribution_estimate = None
            # Initialize section statuses
            section_status = None
            for change in changes:
                if change["type"] == "status_update":
                    if section_status is None:
                        section_status = change["old_status"]
            if section_status is None:
                section_status = "O" if section.percent_open > 0.5 else "C"

            total_value_in_bin = 0
            num_in_bin = 0
            bin_start_pct = 0
            for change in changes:
                if change["type"] == "status_update":
                    if change["old_status"] != section_status:  # Skip erroneous status updates
                        continue
                    section_status = change["new_status"]
                    continue
                if change["type"] == "distribution_estimate_change":
                    latest_raw_demand_distribution_estimate = change
                else:
                    if latest_raw_demand_distribution_estimate is None:
                        continue
                    registration_volume += change["volume_change"]
                if section_status == "O":
                    rel_demand = 0
                elif section_status != "C":
                    rel_demand = 1
                else:
                    param_alpha = latest_raw_demand_distribution_estimate["csdv_gamma_param_alpha"]
                    param_loc = latest_raw_demand_distribution_estimate["csdv_gamma_param_loc"]
                    param_scale = latest_raw_demand_distribution_estimate["csdv_gamma_param_scale"]
                    mean_log_likelihood = latest_raw_demand_distribution_estimate["mean_log_likelihood"]
                    if (param_alpha is None or param_loc is None or param_scale is None or mean_log_likelihood is None):
                        continue
                    rel_demand = stats.gamma.cdf(
                        registration_volume / capacity,
                        param_alpha,
                        param_loc,
                        param_scale,
                    )
                if change["percent_through"] > bin_start_pct + bin_size:
                    if num_in_bin > 0:
                        demand_plot.append((bin_start_pct, total_value_in_bin / num_in_bin))
                    bin_start_pct = change["percent_through"]
                    total_value_in_bin = 0
                    num_in_bin = 0
                total_value_in_bin += rel_demand
                num_in_bin += 1
            if num_in_bin > 0:
                demand_plot.append((bin_start_pct, total_value_in_bin / num_in_bin))
            if bin_start_pct < 1:
                demand_plot.append((1, demand_plot[-1][1]))
            demand_plots_map[semester][section_id] = demand_plot

    recent_demand_plot_semester = (
        max(demand_plots_map.keys()) if len(demand_plots_map) > 0 else None
    )
    recent_demand_plot = (
        average_given_plots(demand_plots_map[recent_demand_plot_semester], bin_size=bin_size)
        if len(demand_plots_map) > 0
        else None
    )

    avg_demand_plot = average_given_plots(demand_plots_map, bin_size=bin_size)
    avg_demand_plot_min_semester = (
        min(demand_plots_map.keys()) if len(demand_plots_map) > 0 else None
    )
    avg_percent_open_plot_num_semesters = len(demand_plots_map)

    return (
        avg_demand_plot,
        avg_demand_plot_min_semester,
        avg_percent_open_plot_num_semesters,
        recent_demand_plot,
        recent_demand_plot_semester,
    )


def avg_and_recent_percent_open_plots(section_map, status_updates_map):
    """
    Aggregate plots of the percentage of sections that were open at each point in time (during
    historical add/drop periods) for the given sections (specified by section_map).
    Percentage-open plots are lists of tuples of the form (percent_through, percentage_open).
    The average plot will average across all sections, and the recent plot will average across
    sections from only the most recent semester.
    Note that section_map should map semester to section id to section object.
    The status_updates_map should map semester to section id to a list of status updates
    for that section (this can be retrieved with the call get_status_updates_map(section_map)).
    The generated plots will have points at increments of step_size in the range [0,1].
    Returns (avg_percent_open_plot, avg_demand_plot_min_semester,
             recent_percent_open_plot, recent_percent_open_plot_semester)
    """

    open_plots = dict()
    # open_plots: maps semester to section id to the plot of when that section was open during
    # the add/drop period (1 if open, 0 if not)

    # Now that all database work has been completed, let's iterate through
    # our semesters and compute open plots for each section
    for semester in section_map.keys():
        if semester < STATUS_UPDATES_RECORDED_SINCE:
            continue
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
            for update in updates:
                if int(update.old_status == "O") != latest_status:
                    # Ignore invalid status updates
                    continue
                latest_status = int(update.new_status == "O")
                open_plot.append((update.percent_through_add_drop_period, latest_status))
            if open_plot[-1][0] < 1:
                open_plot.append((1, latest_status))

            open_plots[semester][section_id] = open_plot

    recent_percent_open_plot_semester = max(open_plots.keys()) if len(open_plots) > 0 else None
    recent_percent_open_plot = (
        average_given_plots(open_plots[max(section_map.keys())]) if len(section_map) > 0 else None
    )

    avg_percent_open_plot = average_given_plots(open_plots)
    avg_percent_open_plot_min_semester = min(open_plots.keys()) if len(open_plots) > 0 else None
    avg_percent_open_plot_num_semesters = len(open_plots)

    return (
        avg_percent_open_plot,
        avg_percent_open_plot_min_semester,
        avg_percent_open_plot_num_semesters,
        recent_percent_open_plot,
        recent_percent_open_plot_semester,
    )
