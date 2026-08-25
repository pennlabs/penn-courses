"""
Shared projection helpers.

Tool results are fed straight back to the model, so values are rendered the way a
student would read them rather than the way the ORM stores them.
"""

from decimal import Decimal


DAY_ORDER = "MTWRFSU"


def number(value):
    """Round a decimal for display, passing through None."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        value = float(value)
    return round(float(value), 2)


def int_to_time(value):
    """
    Render a Meeting's decimal hour (hh.mm) as `10:15 AM`.

    Delegates to the Meeting model so chat and the rest of PCX agree on the format.
    """
    from courses.models import Meeting

    return Meeting.int_to_time(value)


def meeting_times(meetings):
    """
    Render meetings as strings like `MWF 10:15 AM - 11:14 AM`, matching how PCP
    displays them and how `plan.models.Break` stores them.
    """
    by_span = {}
    for meeting in meetings:
        by_span.setdefault((meeting.start, meeting.end), set()).add(meeting.day)
    times = []
    for (start, end), days in sorted(by_span.items()):
        ordered = "".join(sorted(days, key=lambda d: DAY_ORDER.find(d)))
        times.append(f"{ordered} {int_to_time(start)} - {int_to_time(end)}")
    return times


def meeting_spans(meetings):
    """
    Meetings as `(day, start, end)` triples for overlap arithmetic. Times are decimal
    hours, so they compare directly.
    """
    return [(m.day, float(m.start), float(m.end)) for m in meetings]
