import pytest
from django.urls import reverse

from tests.users import factories


@pytest.mark.django_db
class TestUserAdmin:

    def test_get_user_list_admin(self, admin_client) -> None:
        user = factories.UserFactory()
        factories.UserFactory()

        url = reverse('admin:users_user_changelist')

        response = admin_client.get(url)
        assert response.status_code == 200

        qs = response.context.get('cl').queryset
        assert qs.count() == 3
        assert user in qs.all()

    def test_get_user_list_admin_search_filter(self, admin_client) -> None:
        user1 = factories.UserFactory(
            first_name='John', email='johndoe@gmail.com'
        )
        user2 = factories.UserFactory(
            first_name='Bob', email='bobstone@gmail.com'
        )

        url = reverse('admin:users_user_changelist')

        response = admin_client.get(url, {'q': 'John'})
        assert response.status_code == 200
        qs = response.context.get('cl').queryset

        assert qs.count() == 1
        assert user1 in qs.all()
        assert user2 not in qs.all()

    def test_get_user_list_admin_filter(self, admin_client) -> None:
        factories.UserFactory()
        factories.UserFactory()

        url = reverse('admin:users_user_changelist')

        response = admin_client.get(url + '?is_staff__exact=1')
        assert response.status_code == 200
        qs = response.context.get('cl').queryset

        assert qs.count() == 1

    def test_get_user_admin(self, admin_client) -> None:
        user = factories.UserFactory()

        url = reverse('admin:users_user_change', args=(user.pk,))

        response = admin_client.get(url)
        assert response.status_code == 200
