import json
from textwrap import dedent

import requests
from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone
from options.models import get_value

from alert.models import Registration
from courses.models import StatusUpdate


class Command(BaseCommand):
    help = "Get statistics on PCA"

    def add_arguments(self, parser):
        parser.add_argument("days", help="number of days to aggregate.", default=1, type=int)
        parser.add_argument("--slack", action="store_true")

    def handle(self, *args, **options):
        days = options["days"]
        send_to_slack = options["slack"]

        start = timezone.now() - timezone.timedelta(days=days)

        qs = Registration.objects.filter(section__course__semester=get_value("SEMESTER"))

        num_registrations = qs.filter(created_at__gte=start, resubscribed_from__isnull=True).count()
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

        message = dedent(
            f"""
        {f'Penn Course Alert stats in the past {days} day(s)'
         f' since {start.strftime("%H:%M on %d %B, %Y")}'}:
        New registrations: {num_registrations}
        Alerts sent: {num_alerts_sent}
        Manual resubscribes: {num_resubscribe}
        Active auto-resubscribe requests: {num_active_perpetual}
        Status Updates from Penn InTouch: {num_status_updates}
        """
        )

        if send_to_slack:
            url = settings.STATS_WEBHOOK
            print("sending to Slack...")
            requests.post(url, data=json.dumps({"text": message}))
        else:
            print(message)
