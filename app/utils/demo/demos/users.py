import datetime

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

    def get_info(self):
        return [
            'Done. Superuser: email=admin@admin.com pass=admin',
        ]
