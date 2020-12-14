import pytest
from django import forms

from users import forms as user_forms


class TestPasswordChangeForm:
    def test_clean_password_change_form(self):
        pass
        # form = user_forms.PasswordChangeForm()
        # form.password1 = 'password1'
        # form.password2 = 'password2'
        # form.save()
        # form.clean()
        # assert False, form.password1
