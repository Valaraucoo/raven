import datetime

from django.utils import timezone

from users import models as user_models
from users.models import GENDER_CHOICES

GENDER_CHOICES = [x[0] for x in GENDER_CHOICES]


class UsersDemo:
    INFO = 'Done. Superuser: email=admin@admin.com pass=admin \n' \
           '50 Teachers: teacherN@raven.test pass=teacher \n' \
           '100 Students: studentN@raven.test pass=student \n'

    def generate(self):
        self.generate_admin()
        self.generate_teachers()
        self.generate_sudents()

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
        for i in range(50):
            teacher = user_models.User()

            teacher.first_name = f'Name{i}'
            teacher.last_name = f"Last{i}"

            teacher.email = f"teacher{i}@raven.test"
            teacher.address = f"{i}{i}"
            teacher.role = "teacher"

            teacher.date_birth = timezone.now()
            teacher.gender = GENDER_CHOICES[0]

            teacher.is_staff = False
            teacher.is_superuser = False

            teacher.set_password("teacher")
            teacher.save()

    def generate_sudents(self) -> None:
        for i in range(100):
            student = user_models.User()

            student.first_name = f'Name{i}'
            student.last_name = f"Last{i}"

            student.email = f"student{i}@raven.test"
            student.address = f"{i}{i}"
            student.role = "student"

            student.date_birth = timezone.now()
            student.gender = GENDER_CHOICES[0]

            student.is_staff = False
            student.is_superuser = False

            student.set_password("student")
            student.save()
