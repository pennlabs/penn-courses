import json
from textwrap import dedent

import requests
from django.conf import settings
from django.core.management import BaseCommand
from django.db.models import Q
from django.utils import timezone

from alert.models import Registration
from courses.models import StatusUpdate
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

    def handle(self, *args, **options):
        days = options["days"]
        send_to_slack = options["slack"]

        start = timezone.now() - timezone.timedelta(days=days)

        qs = Registration.objects.filter(section__course__semester=get_current_semester())

        num_registrations = qs.filter(created_at__gte=start, resubscribed_from__isnull=True).count()
        num_alerts_sent = qs.filter(notification_sent=True, notification_sent_at__gte=start).count()
        num_resubscribe = qs.filter(
            resubscribed_from__isnull=False,
            created_at__gte=start,
            auto_resubscribe=False,
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
