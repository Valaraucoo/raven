from typing import List

from core import celery
from courses.emails import factories

from . import models


@celery.app.task(shared=True)
def send_new_notice_notification_email(notice: models.CourseNotice, bcc: List[str], email_to: List[str]):
    """
    send_new_notice_notification_email is used to send factories.NewCourseNoticeEmail
    email instance using celery.

    :param notice: models.CourseNotice
    :param bcc: List[str]
    :param email_to: List[str]
    """
    email = factories.NewCourseNoticeEmail(notice, bcc)
    email.send(email_to)


@celery.app.task(shared=True)
def send_new_assignment_notification_email(assignment: models.Assignment, bcc: List[str], email_to: List[str]):
    """
    send_new_assignment_notification_email is used to send factories.NewAssignmentEmail
    email instance using celery.

    :param assignment: models.Assignment
    :param bcc: List[str]
    :param email_to: List[str]
    """
    email = factories.NewAssignmentEmail(assignment, bcc)
    email.send(email_to)
