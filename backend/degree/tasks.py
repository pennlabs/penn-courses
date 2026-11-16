import logging
from smtplib import SMTPRecipientsRefused

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.template import loader
from django.utils import timezone

from alert.alerts import send_email
from degree.models import PDPBetaUser


logger = logging.getLogger(__name__)

SENDER = "Penn Course Alert <team@penncoursealert.com>"


def recipient(person):
    # Penn Labs accounts usually carry the student's email; a PennKey is always an address.
    return person.email or f"{person.username}@upenn.edu"


@shared_task(name="pdp.tasks.send_beta_approval_email")
def send_beta_approval_email(beta_id):
    with transaction.atomic():
        # Locked, so two approvals in quick succession can't both send.
        beta = (
            PDPBetaUser.objects.select_for_update()
            .select_related("person")
            .filter(id=beta_id, status=PDPBetaUser.Status.APPROVED, notified_at__isnull=True)
            .first()
        )
        if beta is None:
            return {"result": "skipped", "task": "pdp.tasks.send_beta_approval_email"}

        to = recipient(beta.person)
        if not settings.SMTP_HOST:
            logger.info("Not emailing %s their PDP beta approval: SMTP isn't configured.", to)
            return {"result": "not configured", "task": "pdp.tasks.send_beta_approval_email"}

        html = loader.render_to_string(
            "degree/beta_approved.html",
            {"first_name": beta.person.first_name, "url": settings.PDP_URL},
        )
        try:
            send_email(
                from_=SENDER,
                to=to,
                subject="You're in the Penn Degree Plan beta!",
                html=html,
            )
        except SMTPRecipientsRefused:
            logger.exception("PDP beta approval email to %s was refused.", to)
            return {"result": "refused", "task": "pdp.tasks.send_beta_approval_email"}

        beta.notified_at = timezone.now()
        beta.save(update_fields=["notified_at"])
    return {"result": "sent", "task": "pdp.tasks.send_beta_approval_email"}
