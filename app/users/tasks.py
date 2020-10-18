from typing import List

from core import celery
from users.emails import factories


@celery.app.task
def send_user_create_notification_email(user, bcc: List[str], email_to: List[str]):
    email = factories.UserCreateEmailFactory(user, bcc)
    email.send(email_to)
