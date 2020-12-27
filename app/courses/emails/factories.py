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


class NewAssignmentEmail(emails.BaseEmailFactory):
    subject_template_name = 'assignment/new_assignment_subject.txt'
    email_template_name = 'assignment/new_assignment.html'

    def __init__(self, assignment, bcc: List[str] = None):
        self.assignment = assignment
        self.bcc = bcc

    def get_context_data(self):
        return {
            'assignment': self.assignment
        }
