from datetime import datetime

from dateutil.tz.tz import gettz
from options.models import get_bool

from courses.util import get_current_semester, get_or_create_add_drop_period
from PennCourses.settings.base import TIME_ZONE


def pca_registration_open():
    """
    Returns True iff PCA should be accepting new registrations.
    """
    current_adp = get_or_create_add_drop_period(semester=get_current_semester())
    return get_bool("REGISTRATION_OPEN", True) and (
        current_adp.end is None
        or datetime.utcnow().replace(tzinfo=gettz(TIME_ZONE)) < current_adp.end
    )


def should_send_pca_alert(course_term, course_status):
    if get_current_semester() != course_term:
        return False
    add_drop_period = get_or_create_add_drop_period(course_term)
    return (
        get_bool("SEND_FROM_WEBHOOK", False)
        and (course_status == "O" or course_status == "C")
        and (
            add_drop_period.end is None
            or datetime.utcnow().replace(tzinfo=gettz(TIME_ZONE)) < add_drop_period.end
        )
    )
