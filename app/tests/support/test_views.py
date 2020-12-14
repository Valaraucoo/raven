import pytest
from django.conf import settings
from django.urls import reverse


class TestTicketCreateView:
    def test_get(self,client):
        url = reverse('support:support-contact')
        response = client.get(url)
        assert response.status_code == 200