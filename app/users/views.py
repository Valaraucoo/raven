from django.shortcuts import render, redirect
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from core import settings


class LoginView(generic.View):
    template_name = 'users/login.html'

    def get_context_data(self, *args, **kwargs):
        return {
            'is_authenticated': self.request.user.is_authenticated
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        if context.get('is_authenticated'):
            messages.info(request, 'jestes juz zalogowany')
            # TODO: redirect to dashboard
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        if context.get('is_authenticated'):
            pass
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        user = authenticate(request, email=email, password=password)
        if user:
            login(request, user)
            if remember == 'on':
                request.session['email'] = email
                request.session['password'] = password
                request.session.set_expiry(1209600)
            else:
                request.session.set_expiry(0)
            messages.info(request, 'Pomyślnie udało się zalogować!')
            # TODO: redirect to dashboard
        else:
            messages.error(request, 'Niestety, nie udało się zalogować, spróbuj ponownie.')
        return render(request, self.template_name, context)


class LogoutView(LoginRequiredMixin, generic.View):
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'See you soon!')
            logout(request)
            request.session['email'] = None
            request.session['password'] = None
            request.session.set_expiry(0)
        return redirect(settings.LOGIN_URL)
