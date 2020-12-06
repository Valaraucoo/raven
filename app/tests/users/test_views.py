import pytest
from django.conf import settings
from django.urls import reverse

from tests.users import factories as users_factories


@pytest.mark.django_db
class TestProfileView:
    def test_get(self, user_client):
        url = reverse('users:profile')
        response = user_client.get(url)
        assert response.status_code == 200

        profile = response.context.get('profile')
        assert profile.full_username == f"{profile.first_name} {profile.last_name} ({profile.email})"

    def test_get_unauthenticated(self, client):
        url = reverse('users:profile')
        response = client.get(url)

        assert response.status_code == 302


class TestProfileDetailView:
    def test_get(self, user_client):
        student = users_factories.StudentFactory()
        teacher = users_factories.TeacherFactory()

        student_url = reverse('users:profile-detail', args=(student.pk,))
        teacher_url = reverse('users:profile-detail', args=(teacher.pk,))

        response_student = user_client.get(student_url)
        response_teacher = user_client.get(teacher_url)

        assert response_student.context.get('profile') == student
        assert response_teacher.context.get('profile') == teacher

        user_id = user_client.session['_auth_user_id']
        url = reverse('users:profile-detail', args=(user_id,))

        response = user_client.get(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestDeleteProfileImageView:
    def test_delete_image_view(self, user_client):
        user = users_factories.StudentFactory(first_name='Bob')
        user_client.force_login(user)

        assert 'defaults/default-picture.png' not in user.image.url

        url = reverse('users:profile-img-delete')
        response = user_client.get(url)

        user.refresh_from_db()

        assert 'defaults/default-picture.png' in user.image.url


@pytest.mark.django_db
class TestDashboardView:
    def test_get_context(self, user_client):
        url = reverse('users:dashboard')
        response = user_client.get(url)
        assert response.status_code == 200

        profile = response.context.get('profile')
        assert profile.full_username == f"{profile.first_name} {profile.last_name} ({profile.email})"

    def test_get_unauthenticated(self, client):
        url = reverse('users:dashboard')
        response = client.get(url)

        assert response.status_code == 302
