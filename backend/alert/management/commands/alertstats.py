import json
from textwrap import dedent

import requests
from django.conf import settings
from django.core.management import BaseCommand
from django.db.models import Q, Count
from django.utils import timezone

from alert.models import Registration
from courses.models import StatusUpdate, Course
from courses.util import get_current_semester


class Command(BaseCommand):
    help = (
        "Get statistics on PCA, and optionally send to Slack (for analytics use only; do "
        "not confuse this script with the recompute_soft_state command, which actually updates "
        "cached statistics)."
    )

    def add_arguments(self, parser):
        parser.add_argument("days", help="number of days to aggregate.", default=1, type=int)
        parser.add_argument("--slack", action="store_true")

    def update_hot_courses(self, qs):
        
        print("updating hot_courses")
        Course.objects.update(is_hot_course = False)
        max_hot_courses = 2

        # course_registration_counts = (
        #     qs
        #     .values('section__course')
        #     .annotate(num_registrations=Count('id'))
        #     .order_by('-num_registrations')
        # )

        # top_alert_courses = [
        #     item['section__course'] for item in course_registration_counts[:max_hot_courses]
        # ]

        # top_alert_courses_set = set(top_alert_courses)

        courses = Course.objects.filter(semester=get_current_semester()).prefetch_related('sections')

        course_scores = []
        for course in courses:
            sections = course.sections.filter(capacity__gt=0)

            enrollment_ratios = []
            alert_registration_ratios = []

            for section in sections:
                capacity = section.capacity or 0
                if capacity <= 0:
                    continue  # Skip sections with zero or negative capacity

                enrollment = section.enrollment or 0
                enrollment_ratio = enrollment / capacity
                enrollment_ratios.append(enrollment_ratio)

                registration_volume = section.registration_volume or 0
                alert_registration_ratio = registration_volume / capacity
                alert_registration_ratios.append(alert_registration_ratio)

            if enrollment_ratios and alert_registration_ratios:
                avg_enrollment_ratio = sum(enrollment_ratios) / len(enrollment_ratios)
                avg_alert_registration_ratio = sum(alert_registration_ratios) / len(alert_registration_ratios)
                score = avg_enrollment_ratio + avg_alert_registration_ratio
                course_scores.append((course.id, score))

       
        top_score_courses = sorted(course_scores, key=lambda x: x[1], reverse=True)[:max_hot_courses]
        top_score_courses_ids = set(course_id for course_id, _ in top_score_courses)

        print("----")
        print(top_score_courses)
        print("----")
        hot_courses_ids = top_alert_courses_set.intersection(top_score_courses_ids)

        print(hot_courses_ids)

        Course.objects.filter(id__in=top_score_courses_ids).update(is_hot_course=True)

        print(f"Updated {len(top_score_courses_ids)} hot courses")

        # ok so now i have the top 100 registered courses (presumably)
        #now what????
        
        #find the ones that were least open the last 2 semesters using pca demand distribution
        #uhhhhhhhhhhhhhhhhh
        # only want ones which csrdv_frac_zero is higher than 0.5 on average for last 2 semesters   

        ## some sort of math to do with the enrollment of the course, the capacity of the course, and the alert_registration of the course.

        #higher enrollment/capacity = hotter
        #higher alert_reg/capacity = hotter
        #average for all sections of a course
        #top courses this way




    def handle(self, *args, **options):
        days = options["days"]
        send_to_slack = options["slack"]

        start = timezone.now() - timezone.timedelta(days=days)

        qs = Registration.objects.filter(section__course__semester=get_current_semester())
        
        

        #cool so I want registration things per thing for each course, its in o1, but this is for a section not course
        # do I want to store section object, course object, course name? what are we doing bruh
        #look into amazon s3
        
       
        num_registrations = qs.filter(created_at__gte=start, resubscribed_from__isnull=True).count()
        
        print(num_registrations)
        
        self.update_hot_courses(qs=qs)
        
        num_alerts_sent = qs.filter(notification_sent=True, notification_sent_at__gte=start).count()
        num_resubscribe = qs.filter(
            resubscribed_from__isnull=False, created_at__gte=start, auto_resubscribe=False
        ).count()
        num_status_updates = StatusUpdate.objects.filter(created_at__gte=start).count()
        num_active_perpetual = qs.filter(
            resubscribed_to__isnull=True,
            auto_resubscribe=True,
            deleted=False,
            cancelled=False,
            notification_sent=False,
        ).count()
        num_cancelled_perpetual = (
            qs.filter(
                resubscribed_to__isnull=True,
                auto_resubscribe=True,
            )
            .filter(Q(deleted=True) | Q(cancelled=True))
            .count()
        )

        message = dedent(
            f"""
        {f'Penn Course Alert stats in the past {days} day(s)'
         f' since {start.strftime("%H:%M on %d %B, %Y")}'}:
        New registrations: {num_registrations}
        Alerts sent: {num_alerts_sent}
        Manual resubscribes: {num_resubscribe}
        Active auto-resubscribe requests: {num_active_perpetual}
        Cancelled auto-resubscribe requests: {num_cancelled_perpetual}
        Status Updates from Penn InTouch: {num_status_updates}
        """
        )

        if send_to_slack:
            url = settings.STATS_WEBHOOK
            print("sending to Slack...")
            requests.post(url, data=json.dumps({"text": message}))
        else:
            print(message)
