import datetime

from django.test import TestCase

from users import models as user_models


class UserModelTest(TestCase):
    def setUp(self) -> None:
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
        self.assertEqual(user.email, self.user_email)

        self.assertEqual(user.is_staff, False)
        self.assertEqual(user.is_student, False)
        self.assertEqual(user.is_teacher, False)

    def test_string_user_model(self) -> None:
        self.assertEqual('John Doe (johndoe@example.com)', str(self.user))
