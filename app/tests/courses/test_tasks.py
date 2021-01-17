import pytest
from django.conf import settings

from courses.tasks import send_new_assignment_notification_email
from tests.courses import factories as course_factories
from tests.users import factories as users_factories


@pytest.mark.django_db
class TestSendCourseTask:
    def test_assignment_notification_email(self, mailoutbox):
        settings.SENDER_EMAIL = 'projekt.io.email@gmail.com'

        user = users_factories.StudentFactory()
        course = course_factories.CourseFactory()
        group = course_factories.GroupFactory(course=course)
        group.save()
        lab = course_factories.LabFactory(course=course, group=group)
        assignment = course_factories.AssignmentFactory(laboratory=lab)
        send_new_assignment_notification_email(assignment, bcc=[], email_to=[user.email])

        assert len(mailoutbox) == 1
        assert mailoutbox[0].bcc == []
        assert mailoutbox[0].to == [user.email]
