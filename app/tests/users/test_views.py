import pytest
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user, login
from django.urls import reverse

from tests.users import factories as users_factories
from users.forms import LoginForm


@pytest.mark.django_db
class TestProfileView:
    def test_get_profile(self, user_client):
        url = reverse('users:profile')
        response = user_client.get(url)
        assert response.status_code == 200

        profile = response.context.get('profile')
        assert profile.full_username == f"{profile.first_name} {profile.last_name} ({profile.email})"

    def test_get_unauthenticated_profile(self, client):
        url = reverse('users:profile')
        response = client.get(url)
        assert response.status_code == 302


class TestProfileDetailView:
    def test_get_profile_detail(self, user_client):
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


class TestProfileEditView:
    def test_post_unauthenticated_edit(self, client):
        url = reverse('users:profile-edit')
        response = client.post(url)
        assert response.status_code == 302

    def test_post_edit(self, user_client):
        url = reverse('users:profile-edit')
        response = user_client.post(url)
        assert response.status_code == 200

    def test_post_password_change(self,user_client):
        url = reverse('users:profile-edit')

    def test_post_edit_data(self, user_client):
        user = users_factories.StudentFactory()
        url = reverse('users:profile-edit')
        data = {
            'address': user.address,
            'description': user.description,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'image': user.image
        }

        response = user_client.post(url, data)
        assert response.status_code == 200


class TestDashboardView:
    def test_get_dashboard(self, user_client):
        url = reverse('users:dashboard')
        response = user_client.get(url)
        assert response.status_code == 200

        user = response.context.get('user')
        assert user.full_username == f"{user.first_name} {user.last_name} ({user.email})"

    def test_get_unauthenticated_dashboard(self, client):
        url = reverse('users:dashboard')
        response = client.get(url)
        assert response.status_code == 302


@pytest.mark.django_db
class TestLoginView:
    def test_get_login(self, user_client):
        url = reverse('users:login')
        response = user_client.get(url)
        assert response.status_code == 302

    def test_get_unauthenticated_login(self, client):
        url = reverse('users:login')
        response = client.get(url)
        assert response.status_code == 200

        # student = users_factories.StudentFactory()
        # user = authenticate(email=student.email, password=student.email)
        # client.force_login(student)
        # user = get_user(client)
        # assert user.is_authenticated
        # response = client.get(url)
        # assert response.status_code == 302

    def test_post_authenticated_login(self, user_client):
        url = reverse('users:login')
        response = user_client.post(url)
        assert response.status_code == 302

    def test_post_login(self, client):
        url = reverse('users:login')
        user = users_factories.StudentFactory()
        user.save()
        data = {
            'email': user.email,
            'password': user.password,
            'remember': True
        }
        #form = LoginForm(data)
        #assert False, form.is_valid()
        # form = response.context.get('form')
        # assert False, form
        response = client.post(url,data)
        assert response.status_code == 200


class TestLogoutView:
    def test_get_logout(self, user_client):
        url = reverse('users:logout')
        response = user_client.get(url)
        assert response.status_code == 302


class TestDeleteProfileImageView:
    def test_delete_image(self, user_client):
        user = users_factories.StudentFactory()
        user_client.force_login(user)

        assert 'defaults/default-picture.png' not in user.image.url

        url = reverse('users:profile-img-delete')
        response = user_client.get(url)
        user.refresh_from_db()

        assert 'defaults/default-picture.png' in user.image.url
