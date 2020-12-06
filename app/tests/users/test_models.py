import datetime

import pytest
from django.urls import reverse

from users import models as user_models


@pytest.mark.django_db
class TestUserModel:
    user = None
    user_email = None

    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        user = user_models.User()
        user.first_name = 'John'
        user.last_name = 'Doe'
        user.date_birth = datetime.date(2020, 9, 18)
        user.email = 'johndoe@example.com'
        user.address = 'Example St 21, New York'
        user.set_password('Password123')
        user.save()
        self.user = user
        self.user_email = user.email

    def test_create_user_model(self) -> None:
        user = user_models.User.objects.get(email=self.user_email)
        assert user.email == self.user_email

        assert not user.is_staff
        assert not user.is_student
        assert not user.is_teacher

    def test_string_user_model(self) -> None:
        assert 'John Doe (johndoe@example.com)' == str(self.user)

    def test_get_user_model_url(self):
        assert "/profile/14" in self.user.get_absolute_url()

    def test_get_user_image_url(self):
        assert "/defaults/default-picture.png" in self.user.get_image_url()

    def test_save_user_model_image(self):
        pass


@pytest.mark.django_db
class TestUserStatus:

    @pytest.fixture(autouse=True)
    def test_user_model_offline_status(self):
        pass