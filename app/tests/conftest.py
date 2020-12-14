import pytest


@pytest.fixture
def user_client(client, admin_user):
    admin_user.is_superuser = False
    admin_user.is_staff = False
    admin_user.first_name = 'John'
    admin_user.last_name = 'Doe'
    admin_user.save()
    client.force_login(admin_user)
    return client
