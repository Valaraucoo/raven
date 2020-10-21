from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.views import generic

from core import settings
from users import forms


class LoginView(generic.View):
    template_name = 'users/login.html'
    form_class = forms.LoginForm

    def get_context_data(self, *args, **kwargs):
        return {
            'is_authenticated': self.request.user.is_authenticated,
            'form': self.form_class,
        }

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)

        email = request.session.get('email')
        password = request.session.get('password')
        user = None

        if email and password:
            user = authenticate(request, email=email, password=password)

        if request.user.is_authenticated or user:
            messages.info(request, 'jestes juz zalogowany')
            # TODO: redirect to dashboard
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        if request.user.is_authenticated:
            # TODO: redirect
            pass
        form = self.form_class(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            email = data.get('email')
            password = data.get('password')
            remember = data.get('remember')

            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                if remember:
                    request.session['email'] = email
                    request.session['password'] = password
                    request.session.set_expiry(1209600)
                else:
                    request.session.set_expiry(0)
                messages.info(request, 'Pomyślnie udało się zalogować!')
                # TODO: redirect to dashboard
            else:
                messages.error(request, 'Niestety, nie udało się zalogować, spróbuj ponownie.')
        else:
            messages.error(request, 'Popraw błędy w formularzu.')
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
