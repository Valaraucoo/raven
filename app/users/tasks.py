from typing import List

from core import celery
from users import models
from users.emails import factories


@celery.app.task(shared=True)
def send_user_create_notification_email(user: models.User, bcc: List[str], email_to: List[str]):
    """
    send_user_create_notification_email is used to send factories.UserActivateEmailFactory
    email instance using celery.

    :param user: models.User
    :param bcc: List[str]
    :param email_to: List[str]
    """
    email = factories.UserActivateEmailFactory(user, bcc)
    email.send(email_to)


@celery.app.task(shared=True)
def send_user_change_password_notification_email(user, bcc: List[str], email_to: List[str]):
    """
    send_user_change_password_notification_email is used to send factories.UserChangePasswordEmailFactory
    email instance using celery.

    :param user: models.User
    :param bcc: List[str]
    :param email_to: List[str]
    """
    email = factories.UserChangePasswordEmailFactory(user, bcc)
    email.send(email_to)
