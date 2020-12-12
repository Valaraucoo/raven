from typing import List

from utils import emails


class NewCourseNoticeEmail(emails.BaseEmailFactory):
    subject_template_name = 'notice/new_notice_subject.txt'
    email_template_name = 'notice/new_notice.html'

    def __init__(self, notice, bcc: List[str] = None):
        self.notice = notice
        self.bcc = bcc

    def get_context_data(self):
        return {
            'notice': self.notice
        }
