from typing import List

from django.conf import settings
from django.core import mail
from django.template import loader


class BaseEmailFactory:
    prefix = 'emails'
    subject_template_name: str = None
    email_template_name: str = None
    email_from: str = None
    cc: List[str] = None
    bcc: List[str] = None
    reply_to: List[str] = None

    def get_context_data(self):
        raise NotImplementedError()

    def get_email_template(self):
        return self.prefix + '/' + self.email_template_name

    def get_subject_template(self):
        return self.prefix + '/' + self.subject_template_name

    def create_email(self, email_to: List[str], *args, **kwargs):
        context = self.get_context_data()
        subject = loader.render_to_string(self.get_subject_template(), context)
        subject = ''.join(subject.splitlines())

        body = loader.render_to_string(self.get_email_template(), context)
        email_from = self.email_from or settings.SENDER_EMAIL

        message = mail.EmailMessage(subject, body, email_from, email_to,
                                    cc=self.cc, bcc=self.bcc, reply_to=self.reply_to)
        message.content_subtype = 'html'
        return message

    def send(self, email_to: List[str]):
        self.create_email(email_to=email_to).send()
