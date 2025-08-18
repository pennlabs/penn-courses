import json
import logging
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from smtplib import SMTP, SMTPRecipientsRefused

import requests
from django.conf import settings
from django.template import loader
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

from PennCourses.settings.production import MOBILE_NOTIFICATION_SECRET


logger = logging.getLogger(__name__)
SEPARATOR = ", "


def send_email(from_, to, subject, html):
    msg = MIMEText(html, "html")
    msg["Subject"] = subject
    msg["From"] = from_
    msg["To"] = to

    with SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
        return True


def send_text(to, text):
    try:
        client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(to=to, from_=settings.TWILIO_NUMBER, body=text)
        if msg.sid is not None:
            return True
    except TwilioRestException:
        logger.exception("Text Error")
        return None


class Alert(ABC):
    def __init__(self, template, reg, close_template=None):
        t = loader.get_template(template)
        meetings_string = ""

        if reg.section.meeting_times:
            try:
                meetings_list = json.loads(reg.section.meeting_times)
                if isinstance(meetings_list, list):
                    meetings_string = SEPARATOR.join(meetings_list)
            except json.JSONDecodeError:
                logger.exception("Error decoding meeting times JSON")

        self.text = t.render(
            {
                "course": reg.section.full_code,
                "brand": "Penn Course Alert",
                "auto_resubscribe": reg.auto_resubscribe,
                "meetings": meetings_string,
            }
        )
        self.close_text = None
        if close_template:
            t = loader.get_template(close_template)
            self.close_text = t.render(
                {
                    "course": reg.section.full_code,
                    "brand": "Penn Course Alert",
                    "auto_resubscribe": reg.auto_resubscribe,
                    "meetings": meetings_string,
                }
            )
        self.registration = reg

    @abstractmethod
    def send_alert(self, close_notification=False):
        pass


class Email(Alert):
    def __init__(self, reg):
        super().__init__("alert/email_alert.html", reg, "alert/email_alert_close.html")

    def send_alert(self, close_notification=False):
        """
        Returns False if notification was not sent intentionally,
        and None if notification was attempted to be sent but an error occurred.
        """
        if self.registration.user is not None and self.registration.user.profile.email is not None:
            email = self.registration.user.profile.email
        elif self.registration.email is not None:
            email = self.registration.email
        else:
            return False

        try:
            if close_notification:
                if not self.close_text:
                    # This should be unreachable
                    return None
                alert_subject = f"{self.registration.section.full_code} has closed."
                alert_text = self.close_text
            else:
                alert_subject = f"{self.registration.section.full_code} is now open!"
                alert_text = self.text
            return send_email(
                from_="Penn Course Alert <team@penncoursealert.com>",
                to=email,
                subject=alert_subject,
                html=alert_text,
            )
        except SMTPRecipientsRefused:
            logger.exception("Email Error")
            return None


class Text(Alert):
    def __init__(self, reg):
        super().__init__("alert/text_alert.txt", reg)

    def send_alert(self, close_notification=False):
        """
        Returns False if notification was not sent intentionally,
        and None if notification was attempted to be sent but an error occurred.
        """
        if close_notification:
            # Do not send close notifications by text
            return False
        if self.registration.user is not None and self.registration.user.profile.push_notifications:
            # Do not send text if push_notifications is enabled
            return False
        if self.registration.user is not None and self.registration.user.profile.phone is not None:
            phone_number = self.registration.user.profile.phone
        elif self.registration.phone is not None:
            phone_number = self.registration.phone
        else:
            return False

        alert_text = self.text
        return send_text(phone_number, alert_text)


class PushNotification(Alert):
    def __init__(self, reg):
        super().__init__("alert/push_notif.txt", reg, close_template="alert/push_notif_close.txt")

    def send_alert(self, close_notification=False):
        """
        Returns False if notification was not sent intentionally,
        and None if notification was attempted to be sent but an error occurred.
        """
        if self.registration.user is not None and self.registration.user.profile.push_notifications:
            # Only send push notification if push_notifications is enabled
            pennkey = self.registration.user.username
            bearer_token = MOBILE_NOTIFICATION_SECRET
            if close_notification:
                if not self.close_text:
                    # This should be unreachable
                    return None
                alert_title = f"{self.registration.section.full_code} just closed."
                alert_body = self.close_text
            else:
                alert_title = f"{self.registration.section.full_code} is now open!"
                alert_body = self.text
            try:
                response = requests.post(
                    "https:/api.pennlabs.org/notifications/send/internal",
                    data={
                        "title": alert_title,
                        "body": alert_body,
                        "pennkey": pennkey,
                    },
                    headers={"Authorization": f"Bearer {bearer_token}"},
                )
                if response.status_code != 200:
                    logger.exception(
                        f"Push Notification {response.status_code} Response: {response.content}"
                    )
                    return None
            except requests.exceptions.RequestException as e:
                logger.exception(f"Push Notification Request Error: {e}")
                return None
            return True
        return False
