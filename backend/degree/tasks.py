import logging
from smtplib import SMTPRecipientsRefused

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.template import loader
from django.utils import timezone

from alert.alerts import send_email
from degree.models import PDPBetaReferral, PDPBetaUser, penn_address


logger = logging.getLogger(__name__)

SENDER = "Penn Course Alert <team@penncoursealert.com>"


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

        to = penn_address(beta.person)
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


@shared_task(name="pdp.tasks.send_referral_email")
def send_referral_email(referral_id):
    task = "pdp.tasks.send_referral_email"
    with transaction.atomic():
        referral = (
            PDPBetaReferral.objects.select_for_update()
            .filter(id=referral_id, status=PDPBetaReferral.Status.APPROVED)
            .first()
        )
        # Several people may have invited the same friend; they hear about it once.
        if referral is None or (
            PDPBetaReferral.objects.select_for_update()
            .filter(pennkey=referral.pennkey, emailed_at__isnull=False)
            .exists()
        ):
            return {"result": "skipped", "task": task}

        if not settings.SMTP_HOST:
            logger.info("Not emailing %s their PDP invite: SMTP isn't configured.", referral.email)
            return {"result": "not configured", "task": task}

        html = loader.render_to_string("degree/beta_referral.html", {"url": settings.PDP_URL})
        try:
            send_email(
                from_=SENDER,
                to=referral.email,
                subject="A friend invited you to try Penn Degree Plan",
                html=html,
            )
        except SMTPRecipientsRefused:
            logger.exception("PDP invite email to %s was refused.", referral.email)
            return {"result": "refused", "task": task}

        referral.emailed_at = timezone.now()
        referral.save(update_fields=["emailed_at"])
    return {"result": "sent", "task": task}
