import datetime
from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import generic
from django.views.generic.detail import DetailView

from core import settings
from users import forms, tasks, models

from courses import models as courses_models


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
    template_name = 'dashboard/main-page.html'

    def get_context_data(self, *args, **kwargs):
        courses = courses_models.Course.objects.none()
        marks = None
        avg_marks = {}
        if self.request.user.is_teacher:
            teacher = models.Teacher.objects.get(email=self.request.user.email)
            courses = teacher.courses_teaching.all()
        else:
            student = models.Student.objects.get(email=self.request.user.email)
            marks = student.courses_marks.all().order_by('-date')[:3]
            for mark in marks:
                if mark.course.name not in avg_marks:
                    avg_marks[mark.course.name] = {
                        'course': mark.course,
                        'sum': 0,
                        'count': 0,
                        'avg': 0
                    }
                avg_marks[mark.course.name]['sum'] += mark.mark
                avg_marks[mark.course.name]['count'] += 1
            for key, value in avg_marks.items():
                avg_marks[key]['avg'] = int(avg_marks[key]['sum'] / avg_marks[key]['count'])
            for grade in student.grades.all():
                courses |= grade.courses.all()
        notices = courses_models.CourseNotice.objects.filter(course__in=courses).order_by('-created_at')[:3]
        lectures = courses_models.Lecture.objects.filter(course__in=courses,
                                                         date__gte=timezone.now(),
                                                         date__lte=timezone.now()+timedelta(days=14)
                                                         ).order_by('date')[:3]
        laboratories = courses_models.Laboratory.objects.filter(course__in=courses,
                                                                date__gte=timezone.now(),
                                                                date__lte=timezone.now()+timedelta(days=14),
                                                                ).order_by('date')
        if self.request.user.is_student:
            laboratories = laboratories.filter(group__students__email__contains=self.request.user.email)
        laboratories = laboratories[:3]

        not_viewed_notices = courses_models.CourseNotice.objects.filter(
            course__in=courses,
            not_viewed__email=self.request.user.email
        ).order_by('-created_at')

        return {
            'user': self.request.user,
            'courses': courses,
            'courses_count': len(courses),
            'notices': notices,
            'now': timezone.now(),
            'lectures': lectures,
            'laboratories': laboratories,
            'not_viewed_notices': not_viewed_notices.count(),
            'marks': marks,
            'avg_marks': avg_marks
        }

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        context = self.get_context_data(*args, **kwargs)
        return render(request, self.template_name, context)


class ScheduleView(LoginRequiredMixin, generic.View):
    template_name = 'dashboard/schedule.html'

    def get_context_data(self, *args, **kwargs):
        courses = courses_models.Course.objects.none()

        if self.request.user.is_teacher:
            teacher = models.Teacher.objects.get(email=self.request.user.email)
            courses = teacher.courses_teaching.all()
        else:
            student = models.Student.objects.get(email=self.request.user.email)
            for grade in student.grades.all():
                courses |= grade.courses.all()
        lectures = courses_models.Lecture.objects.filter(course__in=courses,
                                                         date__gte=timezone.now(),
                                                         date__lte=timezone.now()+timedelta(days=5)
                                                         ).order_by('date')
        laboratories = courses_models.Laboratory.objects.filter(course__in=courses,
                                                                date__gte=timezone.now(),
                                                                date__lte=timezone.now()+timedelta(days=5),
                                                                ).order_by('date')
        if self.request.user.is_student:
            laboratories = laboratories.filter(group__students__email__contains=self.request.user.email)

        today = datetime.date.today()
        schedule = []
        for i in range(5):
            date = today + timedelta(days=i)
            schedule.append({
                'date': date,
                'labs': laboratories.filter(date__day=date.day, date__month=date.month, date__year=date.year),
                'lectures': lectures.filter(date__day=date.day, date__month=date.month, date__year=date.year),
                'is_weekend': date.weekday() >= 5
            })
        return {
            'user': self.request.user,
            'schedule': schedule
        }

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        context = self.get_context_data(*args, **kwargs)
        return render(request, self.template_name, context)


class NoticeView(LoginRequiredMixin, generic.View):
    template_name = 'dashboard/notice.html'

    def get_context_data(self, *args, **kwargs):
        courses = courses_models.Course.objects.none()

        if self.request.user.is_teacher:
            teacher = models.Teacher.objects.get(email=self.request.user.email)
            courses = teacher.courses_teaching.all()
        else:
            student = models.Student.objects.get(email=self.request.user.email)
            for grade in student.grades.all():
                courses |= grade.courses.all()
        notices = courses_models.CourseNotice.objects.filter(course__in=courses).order_by('-created_at')
        notices_obj = []
        for notice in notices:
            notices_obj.append({
                'notice': notice,
                'is_new': self.request.user in notice.not_viewed.all()
            })
        return {
            'user': self.request.user,
            'notices': notices_obj
        }

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        context = self.get_context_data(*args, **kwargs)
        notices = context.get('notices')

        if self.request.user.is_student:
            student = models.Student.objects.get(email=self.request.user.email)
            for notice in notices:
                if student in notice['notice'].not_viewed.all():
                    notice['notice'].not_viewed.remove(student)
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
            messages.info(request, 'Do zobaczenia ponownie!')
            logout(request)
            request.session['email'] = None
            request.session['password'] = None
            request.session.set_expiry(0)
        return redirect(settings.LOGIN_URL)


class MarksView(LoginRequiredMixin, generic.View):
    template_name = 'dashboard/marks.html'

    def get_context_data(self, *args, **kwargs):
        student = models.Student.objects.get(email=self.request.user.email)
        marks = student.courses_marks.all().order_by('-date')
        avg_marks = {}
        for course in courses_models.Course.objects.filter(grade__students__email=student.email):
            if course.name not in avg_marks:
                final_mark = student.courses_final_marks.filter(course=course).first()
                avg_marks[course.name] = {
                    'course': course,
                    'sum': 0,
                    'count': 0,
                    'avg': 0,
                    'final_mark': final_mark
                }
            course_marks = student.courses_marks.filter(course=course)
            for mark in course_marks:
                avg_marks[course.name]['sum'] += mark.mark
                avg_marks[course.name]['count'] += 1
        for key, value in avg_marks.items():
            try:
                avg_marks[key]['avg'] = int(avg_marks[key]['sum'] / avg_marks[key]['count'])
            except ZeroDivisionError:
                avg_marks[key]['avg'] = ''

        return {
            'user': self.request.user,
            'marks': marks,
            'avg_marks': avg_marks
        }

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)
        if self.request.user.is_teacher:
            return redirect('users:dashboard')
        context = self.get_context_data(*args, **kwargs)

        marks = context['marks']
        if request.GET:
            course = request.GET.get('course')
            if course:
                context['query'] = course
                marks = marks.filter(course__name__icontains=course)
        context['marks'] = marks
        return render(request, self.template_name, context)
