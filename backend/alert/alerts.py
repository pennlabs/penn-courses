import logging
from abc import ABC, abstractmethod
from email.mime.text import MIMEText
from smtplib import SMTP, SMTPRecipientsRefused

from django.conf import settings
from django.template import loader
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client

import requests


logger = logging.getLogger(__name__)


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
        return False


class Alert(ABC):
    def __init__(self, template, reg):
        t = loader.get_template(template)
        self.text = t.render({"course": reg.section.full_code, "brand": "Penn Course Alert",})
        self.registration = reg

    @abstractmethod
    def send_alert(self):
        pass


class Email(Alert):
    def __init__(self, reg):
        super().__init__("alert/email_alert.html", reg)

    def send_alert(self):
        if self.registration.user is not None and self.registration.user.profile.email is not None:
            email = self.registration.user.profile.email
        elif self.registration.email is not None:
            email = self.registration.email
        else:
            return False
        try:
            return send_email(
                from_="Penn Course Alert <team@penncoursealert.com>",
                to=email,
                subject="%s is now open!" % self.registration.section.full_code,
                html=self.text,
            )
        except SMTPRecipientsRefused:
            logger.exception("Email Error")
            return False


class Text(Alert):
    def __init__(self, reg):
        super().__init__("alert/text_alert.txt", reg)

    def send_alert(self):
        if self.registration.user is not None and self.registration.user.profile.phone is not None:
            phone_number = self.registration.user.profile.phone
        elif self.registration.phone is not None:
            phone_number = self.registration.phone
        else:
            return False

        return send_text(phone_number, self.text)


class PushNotification(Alert):
    def __init__(self, reg):
        super().__init__("alert/push_notif.txt", reg)

    def send_alert(self):
        if self.registration.push_notifications:
            pennkey = self.registration.user.username
            bearer_token = str(10101)
            r = requests.post(
                "https:/api.pennlabs.org/notifications/send/internal",
                data={
                    "title": "%s is now open!" % self.registration.section.full_code,
                    "body": self.text,
                    "pennkey": pennkey,
                },
                headers={"Authorization": "Bearer %s" + bearer_token},
            )

        return False
