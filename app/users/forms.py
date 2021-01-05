from django import forms
from django.core.exceptions import ValidationError

tailwind_form = 'appearance-none relative block w-full px-3 py-2 border border-gray-300 ' \
                'placeholder-gray-500 text-gray-900 focus:outline-none focus:shadow-outline-blue ' \
                'focus:border-blue-300 focus:z-10 sm:text-sm sm:leading-5 '

tailwind_form2 = 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4' \
                 ' mb-3 leading-tight focus:outline-none focus:bg-white focus:border-gray-500 '


class LoginForm(forms.Form):
    email = forms.CharField(max_length=100, widget=forms.EmailInput(attrs={
        'class': tailwind_form + 'rounded-t-md',
        'placeholder': 'Adres Email',
    }))
    password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={
        'class': tailwind_form + 'rounded-b-md',
        'placeholder': 'Hasło',
    }))
    remember = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-checkbox h-4 w-4 text-indigo-600 transition duration-150 ease-in-out',
    }))


class PasswordChangeForm(forms.Form):
    password1 = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={
        'class': tailwind_form2,
        'placeholder': '***********',
    }))
    password2 = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={
        'class': tailwind_form2,
        'placeholder': '***********',
    }))

    def clean(self):
        cleaned_data = super().clean()
        pass1 = cleaned_data.get('password1')
        pass2 = cleaned_data.get('password2')
        if (pass1 or pass2) and pass1 != pass2:
            raise ValidationError("Hasła się nie zgadzają.")
