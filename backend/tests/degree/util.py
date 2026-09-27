from django.db.models.signals import post_save
from options.models import Option

from alert.models import AddDropPeriod
from courses.util import invalidate_current_semester_cache


TEST_SEMESTER = "2023C"


def set_semester():
    post_save.disconnect(
        receiver=invalidate_current_semester_cache,
        sender=Option,
        dispatch_uid="invalidate_current_semester_cache",
    )
    Option(key="SEMESTER", value=TEST_SEMESTER, value_type="TXT").save()
    AddDropPeriod(semester=TEST_SEMESTER).save()
