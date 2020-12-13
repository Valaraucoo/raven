from typing import List

from core import celery
from courses.emails import factories


@celery.app.task(shared=True)
def send_new_notice_notification_email(notice, bcc: List[str], email_to: List[str]):
    email = factories.NewCourseNoticeEmail(notice, bcc)
    email.send(email_to)
