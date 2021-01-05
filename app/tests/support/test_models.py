import pytest
from django.conf import settings
from django.urls import reverse

from support import models as support_models
from tests.users import factories as users_factories


@pytest.mark.django_db
class TestSupportTicket:
    def test_string_support_ticket(self,client):
        student = users_factories.StudentFactory()
        fullname = f"{student.first_name} {student.last_name}" if student.is_authenticated else student.full_username
        ticket = support_models.SupportTicket(email=student.email, issuer_fullname=fullname, description='description',
                                              category=support_models.SupportCategories.OTHER, status=support_models.SupportStatus.PROCESSING)
        assert f"[{ticket.category}][{ticket.status}] {ticket.email}" == str(ticket)
