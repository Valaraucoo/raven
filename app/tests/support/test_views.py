import pytest
from django.urls import reverse

from tests.users import factories as users_factories


@pytest.mark.django_db
class TestTicketCreateView:
    def test_get(self,client):
        url = reverse('support:support-contact')
        response = client.get(url)
        assert response.status_code == 200

    def test_post(self,client):
        url = reverse('support:support-contact')
        response = client.post(url)
        assert response.status_code == 200

        user = users_factories.StudentFactory()

        data = {
            "email": user.email,
            "category": '1',
            "fullname": f'{user.first_name} {user.last_name}',
            "description": "problem"
        }

        response = client.post(url, data=data)
        assert response.status_code == 200

        data['category'] = '2'

        response = client.post(url, data=data)
        assert response.status_code == 200

        data['category'] = '3'

        response = client.post(url, data=data)
        assert response.status_code == 200

        data['category'] = '0'

        response = client.post(url, data=data)
        assert response.status_code == 200
