import datetime

from tests.users import factories as user_factories
from users import models as user_models


class UsersDemo:
    def generate(self):
        self.generate_admin()

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

    def generate_teachers(self) -> None:
        for i in range(10):
            teacher = user_factories.TeacherFactory(email=f"teacher{i}@raven.test")
            teacher.email = f"teacher{i}@raven.test"
            teacher.set_passowrd("teacher")
            teacher.save()

    def generate_sudents(self) -> None:
        for i in range(30):
            student = user_factories.StudentFactory(email=f"student{i}@raven.test")
            student.email = f"student{i}@raven.test"
            student.set_passowrd("student")
            student.save()

    def get_info(self):
        return [
            'Done. Superuser: email=admin@admin.com pass=admin',
            '\t 10 Teachers: email=teacherN@raven.test pass=teacher',
            '\t 30 Students: email=student@raven.test pass=student'
        ]
