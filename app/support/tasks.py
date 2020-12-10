from typing import List

from core import celery
from support.emails import factories


@celery.app.task(shared=True)
def send_support_notification_email(user_email, fullname, bcc: List[str], email_to: List[str]):
    email = factories.SupportEmail(user_email, fullname, bcc)
    email.send(email_to)
