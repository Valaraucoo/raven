import factory
import factory.fuzzy as fuzzy
from django.core.files.base import ContentFile

from users import models as user_models
from users.models import GENDER_CHOICES

GENDER_CHOICES = [x[0] for x in GENDER_CHOICES]


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = user_models.User

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')

    email = factory.Faker('email')
    address = factory.Faker('address')

    date_birth = factory.Faker('date')
    gender = fuzzy.FuzzyChoice(GENDER_CHOICES)

    is_staff = False
    is_superuser = False

    description = fuzzy.FuzzyText(length=30)

    image = factory.LazyAttribute(
        lambda _: ContentFile(
            factory.django.ImageField()._make_data(
                {'width': 200, 'height': 200}
            ), 'example.jpg'
        )
    )
    first_login = fuzzy.FuzzyChoice([True, False])


class StudentFactory(UserFactory):
    class Meta:
        model = user_models.Student
    role = 'student'


class TeacherFactory(UserFactory):
    class Meta:
        model = user_models.Teacher
    role = 'teacher'


class AdminUserFactory(UserFactory):
    is_staff = True
    is_superuser = True
