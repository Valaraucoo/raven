import datetime

from users import models as user_models
from tests.users import factories as user_factories


class UsersDemo:
    def generate(self):
        self.generate_admin()
        self.generate_students()
        self.generate_teachers()

    def generate_admin(self) -> None:
        user = user_models.User()
        user.first_name = 'John'
        user.last_name = 'Doe'
        user.email = 'admin@admin.com'
        user.date_birth = datetime.date(1990, 1, 1)
        user.address = 'Warszawa'
        user.is_staff = True
        user.is_superuser = True
        user.role = 'teacher'
        user.set_password('admin')
        user.save()

    def generate_students(self) -> None:
        for i in range(10):
            user_factories.UserFactory(
                email=f'student{i}@gmail.com', password='example123', role='student'
            )

    def generate_teachers(self) -> None:
        for i in range(5):
            user_factories.UserFactory(
                email=f'teacher{i}@gmail.com', password='example123', role='teacher'
            )

    def get_info(self):
        return [
            'Done. Superuser: email=admin@admin.com pass=admin',
            '      Students:  email=student<N>@gmail.com pass=example123',
            '      Teachers:  email=teacher<N>@gmail.com pass=example123',
        ]
