from django import forms


class LoginForm(forms.Form):
    email = forms.CharField(max_length=100, widget= forms.EmailInput(attrs={
        'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 '
                 'placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:shadow-outline-blue '
                 'focus:border-blue-300 focus:z-10 sm:text-sm sm:leading-5',
        'placeholder': 'Adres Email',
    }))
    password = forms.CharField(max_length=100, widget=forms.PasswordInput(attrs={
        'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 '
                 'placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:shadow-outline-blue '
                 'focus:border-blue-300 focus:z-10 sm:text-sm sm:leading-5',
        'placeholder': 'Hasło',
    }))
    remember = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={
        'class': 'form-checkbox h-4 w-4 text-indigo-600 transition duration-150 ease-in-out',
    }))
