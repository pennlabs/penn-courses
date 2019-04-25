from abc import ABC, abstractmethod
from smtplib import SMTP, SMTPRecipientsRefused
from email.mime.text import MIMEText
import logging

from django.template import loader
from django.conf import settings

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)


def send_email(from_, to, subject, html):
    msg = MIMEText(html, 'html')
    msg['Subject'] = subject
    msg['From'] = from_
    msg['To'] = to

    with SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)
        return True


class Alert(ABC):
    def __init__(self, template, reg):
        t = loader.get_template(template)
        self.text = t.render({
            'course': reg.section.normalized,
            'signup_url': reg.resub_url,
            'brand': 'Penn Course Alert'
        })
        self.registration = reg

    @abstractmethod
    def send_alert(self):
        pass


class Email(Alert):
    def __init__(self, reg):
        super().__init__('email_alert.html', reg)

    def send_alert(self):
        if self.registration.email is None:
            return False
        try:
            return send_email(from_='Penn Course Alert <team@penncoursealert.com>',
                              to=self.registration.email,
                              subject='%s is now open!' % self.registration.section.normalized,
                              html=self.text)
        except SMTPRecipientsRefused:
            logger.exception('Email Error')
            return False


class Text(Alert):
    def __init__(self, reg):
        super().__init__('text_alert.txt', reg)

    def send_alert(self):
        if self.registration.phone is None:
            return False

        try:
            client = Client(settings.TWILIO_SID, settings.TWILIO_AUTH_TOKEN)
            msg = client.messages.create(
                to=self.registration.phone,
                from_=settings.TWILIO_NUMBER,
                body=self.text
            )
            if msg.sid is not None:
                return True
        except TwilioRestException:
            logger.exception('Text Error')
            return False
