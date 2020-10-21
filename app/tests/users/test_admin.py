from django.test import Client, TestCase
from django.urls import reverse

from tests.users import factories


class UserAdminTest(TestCase):
    def setUp(self) -> None:
        self.user = factories.AdminUserFactory(
            first_name='Adam', last_name='Smith', email='adamsmith@yahoo.com'
        )
        self.client = Client()
        self.client.force_login(self.user)

    def test_get_user_list_admin(self) -> None:
        factories.UserFactory()
        factories.UserFactory()

        url = reverse('admin:users_user_changelist')

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        qs = response.context.get('cl').queryset
        self.assertEqual(qs.count(), 3)
        self.assertIn(self.user, qs.all())

        new_user = factories.UserFactory()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        qs = response.context.get('cl').queryset
        self.assertEqual(qs.count(), 4)
        self.assertIn(new_user, qs.all())

    def test_get_user_list_admin_search_filter(self) -> None:
        user1 = factories.UserFactory(
            first_name='John', email='johndoe@gmail.com'
        )
        user2 = factories.UserFactory(
            first_name='Bob', email='bobstone@gmail.com'
        )

        url = reverse('admin:users_user_changelist')

        response = self.client.get(url, {'q': 'John'})
        self.assertEqual(response.status_code, 200)
        qs = response.context.get('cl').queryset

        self.assertEqual(qs.count(), 1)
        self.assertIn(user1, qs.all())
        self.assertNotIn(user2, qs.all())

    def test_get_user_list_admin_filter(self) -> None:
        factories.UserFactory()
        factories.UserFactory()

        url = reverse('admin:users_user_changelist')

        response = self.client.get(url + '?is_staff__exact=1')
        self.assertEqual(response.status_code, 200)
        qs = response.context.get('cl').queryset

        self.assertEqual(qs.count(), 1)
        self.assertIn(self.user, qs.all())

    def test_get_user_admin(self) -> None:
        user = factories.UserFactory()

        url = reverse('admin:users_user_change', args=(user.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
