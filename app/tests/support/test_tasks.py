import pytest
from django.conf import settings

from support.tasks import send_support_notification_email
from tests.users import factories as users_factories


@pytest.mark.django_db
class TestSendSupportTask:
    def test_support_notification_email(self, mailoutbox):
        settings.SENDER_EMAIL = 'projekt.io.email@gmail.com'

        user = users_factories.StudentFactory()
        send_support_notification_email(user_email=user.email, fullname=f'{user.first_name} {user.last_name}', bcc=[], email_to=[user.email])

        assert len(mailoutbox) == 1
        assert mailoutbox[0].bcc == []
        assert mailoutbox[0].to == [user.email]
