from django import forms

from . import models


tailwind_form = 'appearance-none block w-full bg-gray-200 text-gray-700 border border-gray-200 rounded py-3 px-4' \
                ' mb-3 leading-tight focus:outline-none focus:bg-white focus:border-gray-500'


class TicketCreateForm(forms.Form):
    email = forms.CharField(max_length=100, required=False,widget=forms.EmailInput(attrs={
        'class': tailwind_form,
        'placeholder': 'Adres Email',
    }))
    fullname = forms.CharField(max_length=100, required=False,widget=forms.TextInput(attrs={
        'class': tailwind_form,
        'placeholder': 'Imię i nazwisko',
    }))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'placeholder': 'Opis problemu',
        'class': tailwind_form,
        'cols': 30,
        'rows': 5
    }))
