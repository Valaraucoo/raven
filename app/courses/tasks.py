from typing import List

from core import celery
from courses.emails import factories

from . import models


@celery.app.task(shared=True)
def send_new_notice_notification_email(notice: models.CourseNotice, bcc: List[str], email_to: List[str]):
    email = factories.NewCourseNoticeEmail(notice, bcc)
    email.send(email_to)


@celery.app.task(shared=True)
def send_new_assignment_notification_email(assignment: models.Assignment, bcc: List[str], email_to: List[str]):
    email = factories.NewAssignmentEmail(assignment, bcc)
    email.send(email_to)
