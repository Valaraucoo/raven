from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.detail import DetailView
from django.shortcuts import redirect, render
from django.views import generic

from core import settings
from users import forms
from users import tasks


def delete_profile_image(request):
    request.user.image = settings.DEFAULT_USER_IMAGE
    request.user.save()
    messages.info(request, 'Twoje zdjęcie zostało usunięte')
    return redirect('users:profile-edit')


class ProfileView(generic.View, LoginRequiredMixin):
    template_name = 'dashboard/profile.html'

    def get_context_data(self, *args, **kwargs):
        return {
            'profile': self.request.user
        }

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        context = self.get_context_data(*args, **kwargs)
        return render(request, self.template_name, context)


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = get_user_model()
    template_name = 'dashboard/profile-detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.object
        return context

    def get(self, request, *args, **kwargs):
        if request.user == self.get_object():
            return redirect('users:profile')
        return super().get(request, *args, **kwargs)


class ProfileEditView(ProfileView):
    template_name = 'dashboard/profile-edit.html'
    form_class = forms.PasswordChangeForm

    def get_context_data(self, *args, **kwargs):
        return {
            'profile': self.request.user,
            'password_change_form': self.form_class,
        }

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        context = self.get_context_data(*args, **kwargs)
        password_change_form = self.form_class(request.POST)
        data = password_change_form.data
        if password_change_form.is_valid():
            password = data.get('password1')
            if len(password) > 5:
                user.set_password(password)
                user.save()
                tasks.send_user_change_password_notification_email(
                    user=user, bcc=[], email_to=[user.email]
                )
                messages.info(request, 'Pomyślnie zmieniono hasło!')
            else:
                messages.error(request, 'Hasło musi być dłuższe niż 5 znaków!')
            return render(request, self.template_name, context)
        elif data.get('password1') != data.get('password2'):
            messages.error(request, 'Hasła muszą być takie same!')
            return render(request, self.template_name, context)

        data = request.POST
        if data:
            address = data.get('address')
            description = data.get('description')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            image = request.FILES.get('image')

            if description:
                user.description = description
            if address:
                user.address = address
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if image:
                user.image = image
            messages.info(request, 'Pomyślnie zaktualizowano profil!')

        user.save()
        return render(request, self.template_name, context)


class DashboardView(generic.View, LoginRequiredMixin):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, *args, **kwargs):
        return {
            'user': self.request.user,
        }

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        context = self.get_context_data(*args, **kwargs)
        return render(request, self.template_name, context)


class LoginView(generic.View):
    template_name = 'users/login.html'
    form_class = forms.LoginForm

    def get_context_data(self, *args, **kwargs):
        return {
            'is_authenticated': self.request.user.is_authenticated,
            'form': self.form_class,
        }

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('users:dashboard')

        context = self.get_context_data(*args, **kwargs)

        email = request.session.get('email')
        password = request.session.get('password')
        user = None

        if email and password:
            user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)
            if request.user.is_authenticated:
                messages.info(request, 'Jestes juz zalogowany!')
                return redirect('users:dashboard')
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('users:dashboard')
        context = self.get_context_data(*args, **kwargs)
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
                if request.user.first_login:
                    messages.info(request, 'Zalogowałeś się po raz pierwszy! Zmień swoje hasło!')
                    request.user.first_login = False
                    request.user.save()
                    tasks.send_user_create_notification_email(request.user, bcc=[], email_to=[request.user.email])
                    return redirect('users:profile-edit')
                messages.info(request, 'Pomyślnie udało się zalogować!')
                return redirect('users:dashboard')
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
