from typing import List

from utils import emails


class SupportEmail(emails.BaseEmailFactory):
    subject_template_name = 'support/ticket_create_subject.txt'
    email_template_name = 'support/ticket_create_email.html'

    def __init__(self, user_email, fullname, bcc: List[str] = None):
        self.user_email = user_email
        self.fullname = fullname
        self.bcc = bcc

    def get_context_data(self):
        return {
            'user_email': self.user_email,
            'fullname': self.fullname,
        }
