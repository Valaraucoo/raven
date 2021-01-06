from typing import List

from utils import emails


class UserActivateEmailFactory(emails.BaseEmailFactory):
    """
    UserActivateEmailFactory is used to create and send email instances
    about account activation.
    """
    subject_template_name = 'users/user_create_subject.txt'
    email_template_name = 'users/user_create_email.html'

    def __init__(self, user, bcc: List[str] = None):
        self.user = user
        self.bcc = bcc

    def get_context_data(self):
        return {
            'user': self.user,
        }


class UserChangePasswordEmailFactory(UserActivateEmailFactory):
    """
    UserChangePasswordEmailFactory is used to create and send email instances
    about changing password.
    """
    subject_template_name = 'users/user_change_password_subject.txt'
    email_template_name = 'users/user_change_password_email.html'
