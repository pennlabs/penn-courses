import json
from textwrap import dedent

import requests
from django.conf import settings
from django.core.management import BaseCommand
from django.utils import timezone

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

        num_registrations = Registration.objects.filter(created_at__gte=start).count()
        num_alerts_sent = Registration.objects.filter(
            notification_sent=True, notification_sent_at__gte=start
        ).count()
        num_resubscribe = Registration.objects.filter(
            resubscribed_from__isnull=False, created_at__gte=start
        ).count()
        num_status_updates = StatusUpdate.objects.filter(created_at__gte=start).count()

        message = dedent(
            f"""
        {f'Penn Course Alert stats in the past {days} day(s)'
         f' since {start.strftime("%H:%M on %d %B, %Y")}'}:
        New registrations: {num_registrations}
        Alerts sent: {num_alerts_sent}
        Resubscribes: {num_resubscribe}
        Status Updates from Penn InTouch: {num_status_updates}
        """
        )

        if send_to_slack:
            url = settings.STATS_WEBHOOK
            print("sending to Slack...")
            requests.post(url, data=json.dumps({"text": message}))
        else:
            print(message)
