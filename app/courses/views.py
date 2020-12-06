import datetime
from typing import List

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.views.generic.detail import DetailView

from courses import forms, models
from users import models as users_models


class CoursesGuardianPermissionMixin(LoginRequiredMixin, DetailView):
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_student:
            student = users_models.Student.objects.get(email=user.email)
            if student not in self.get_object().grade.students.all():
                return redirect('courses:courses')
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().teachers.all():
                return redirect('courses:courses')
        return super().get(self, request, *args, **kwargs)


class CourseView(LoginRequiredMixin, generic.View):
    template_name = 'courses/courses.html'

    def get_context_data(self, **kwargs):
        user = self.request.user
        courses: List[int] = []

        if user.is_student:
            student = users_models.Student.objects.get(pk=user.pk)
            for grade in student.grades.all():
                for course in grade.courses.all():
                    courses.append(course.pk)
        elif user.is_teacher:
            teacher = users_models.Teacher.objects.get(pk=user.pk)
            for course in teacher.courses_teaching.all():
                courses.append(course.pk)

        courses_qs = models.Course.objects.filter(pk__in=courses)

        context = {
            'courses': courses_qs,
            'has_courses': len(courses_qs) > 0
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        courses_qs = context.get('courses')

        query = request.GET
        if 'name' in query:
            name = query.get('name')
            courses_qs = courses_qs.filter(name__icontains=name)
            context['q_name'] = name
        if 'teacher' in query:
            teacher = query.get('teacher')
            courses_qs = courses_qs.filter(head_teacher__last_name__icontains=teacher)
            context['q_teacher'] = teacher
        if 'has_exam' in query:
            has_exam = query.get('has_exam')
            if has_exam == '1':
                courses_qs = courses_qs.filter(has_exam=True)
            elif has_exam == '2':
                courses_qs = courses_qs.filter(has_exam=False)
            context['has_exam'] = has_exam
        context['courses'] = courses_qs
        return render(request, self.template_name, context)


class CoursesDetailView(CoursesGuardianPermissionMixin):
    model = models.Course
    template_name = 'courses/courses-detail.html'
    slug_field = 'slug'
    slug_url_kwarg = 'the_slug'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_lectures'] = [lecture for lecture in self.object.lectures.all() if lecture.is_available]
        context['available_labs'] = [lab for lab in self.object.laboratories.all() if lab.is_available]
        context['student_without_groups_emails'] = [student.email for student in self.object.students_without_groups]
        return context


class CourseGroupJoinListView(CoursesDetailView):
    template_name = 'courses/courses-group-join.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = self.object.groups.all()
        return context


def course_group_join_view(request, the_slug, num):
    user = request.user
    if not user.is_authenticated:
        return redirect('courses:courses')
    if user.is_teacher:
        return redirect('courses:courses-detail', the_slug=the_slug)
    course = models.Course.objects.get(slug=the_slug)
    if course:
        course_group = course.groups.all()[num]
        if course_group:
            student = users_models.Student.objects.get(email=user.email)
            if student in course.grade.students.all() and student in course.students_without_groups:
                course_group.students.add(student)
                course_group.save()
                messages.info(request, 'Pomyślnie dołączyłeś do grupy.')
                return redirect('courses:courses-detail', the_slug=the_slug)
    messages.error(request, 'Spróbuj ponownie.')
    return redirect('courses:courses')


class CourseEditView(CoursesDetailView):
    template_name = 'courses/courses-detail-edit.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lectures'] = self.object.lectures.all()
        return context

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().teachers.all():
                return redirect('courses:courses')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = request.user
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().teachers.all():
                return redirect('courses:courses')

        course = models.Course.objects.get(slug=kwargs.get('the_slug'))
        data = request.POST
        if data:
            course_name = data.get('name')
            course_description = data.get('description')
            if course_name:
                course.name = course_name
            if course_description:
                course.description = course_description
            course.save()
            messages.info(request, 'Pomyślnie zaktualizowano kurs!')

        return super().get(request, *args, **kwargs)


class LectureDetailView(DetailView):
    template_name = 'courses/lecture-detail.html'
    model = models.Lecture
    context_object_name = 'lecture'

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect('courses:courses')
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().course.teachers.all():
                return redirect('courses:courses')
        if user.is_student:
            student = users_models.Student.objects.get(email=user.email)
            if student not in self.get_object().course.grade.students.all():
                return redirect('courses:courses')
        return super().get(request, *args, **kwargs)


class LaboratoryDetailView(LectureDetailView):
    template_name = 'courses/laboratory-detail.html'
    model = models.Laboratory
    context_object_name = 'laboratory'


class LectureEditView(DetailView):
    template_name = 'courses/lecture-edit.html'
    model = models.Lecture
    context_object_name = 'lecture'

    def get_context_data(self, **kwargs):
        lecture = self.get_object()
        context = {
            'lecture': lecture,
            'form': forms.LectureCreateForm(initial={
                'title': lecture.title,
                'date': lecture.date.strftime('%d.%m.%Y'),
                'time': lecture.date.strftime('%H:%M'),
                'duration': lecture.duration.seconds // 60,
                'description': lecture.description,
                'show': lecture.show,
                'meeting': lecture.create_event
            })
        }
        return context

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user.is_student:
            return redirect('courses:courses')
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().course.teachers.all():
                return redirect('courses:courses')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user.is_student:
            return redirect('courses:courses')
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().course.teachers.all():
                return redirect('courses:courses')

        context = self.get_context_data(**kwargs)
        form = forms.LectureCreateForm(request.POST)

        if form.is_valid():
            title = form.data.get('title')
            date = form.data.get('date')
            time = form.data.get('time')
            duration = form.data.get('duration')
            localization = request.POST.get('localization', 'Remote')
            description = form.data.get('description', '')
            show = form.data.get('show', False)
            meeting = form.data.get('meeting', False)

            try:
                date_parsed = datetime.datetime.strptime(date, '%d.%m.%Y')
            except Exception:
                date_parsed = None

            try:
                time_parsed = datetime.datetime.strptime(time, '%H:%M')
            except Exception:
                time_parsed = None

            try:
                minutes = int(duration)
                duration = datetime.timedelta(minutes=minutes)
            except Exception:
                duration = None

            if title and date_parsed and time_parsed and duration and localization:
                lecture = context['lecture']
                lecture.title = title
                lecture.date = date_parsed + datetime.timedelta(hours=time_parsed.hour, minutes=time_parsed.minute)
                lecture.duration = duration
                lecture.location = localization
                lecture.description = description
                lecture.show = show == 'on'
                lecture.create_event = meeting == 'on'

                #TODO: update wydarzenia w Google Calendar
                #TODO: powiadomienie (?) do prowadzącego, że utworzył wykład
                #TODO: pliki (?)
                lecture.save()
                messages.info(request, 'Pomyślnie zaktualizowano wykład!')
                return redirect('courses:lectures-edit', pk=lecture.pk)
            else:
                messages.error(request, 'Uzupełnij poprawnie formularz!')
        else:
            messages.error(request, 'Uzupełnij poprawnie formularz!')
        return render(request, self.template_name, context)


class LectureCreateView(DetailView):
    template_name = 'courses/lecture-create.html'
    model = models.Course
    slug_field = 'slug'
    slug_url_kwarg = 'the_slug'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        return {
            'course': self.get_object(),
            'form': forms.LectureCreateForm
        }

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user.is_student:
            return redirect('courses:courses')
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().teachers.all():
                return redirect('courses:courses')

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated or user.is_student:
            return redirect('courses:courses')
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().teachers.all():
                return redirect('courses:courses')

        form = forms.LectureCreateForm(request.POST)

        if form.is_valid():
            title = form.data.get('title')
            date = form.data.get('date')
            time = form.data.get('time')
            duration = form.data.get('duration')
            localization = request.POST.get('localization', 'Remote')
            description = form.data.get('description', '')
            show = form.data.get('show', False)
            meeting = form.data.get('meeting', False)

            try:
                date_parsed = datetime.datetime.strptime(date, '%d.%m.%Y')
            except Exception:
                date_parsed = None

            try:
                time_parsed = datetime.datetime.strptime(time, '%H:%M')
            except Exception:
                time_parsed = None

            try:
                minutes = int(duration)
                duration = datetime.timedelta(minutes=minutes)
            except Exception:
                duration = None

            if title and date_parsed and time_parsed and duration and localization:
                lecture = models.Lecture.objects.create(
                    course=self.get_object(),
                    title=title,
                    location=localization,
                    description=description,
                    date=date_parsed + datetime.timedelta(hours=time_parsed.hour, minutes=time_parsed.minute),
                    duration=duration,
                    show=show == 'on',
                    create_event=meeting == 'on',
                )
                #TODO: tworzenie wydarzenia w Google Calendar
                #TODO: powiadomienie (?) do prowadzącego, że utworzył wykład
                messages.info(request, 'Pomyślnie utworzono nowy wykład!')
                return redirect('courses:lectures-detail', pk=lecture.pk)
            else:
                messages.error(request, 'Uzupełnij poprawnie formularz!')
        else:
            messages.error(request, 'Uzupełnij poprawnie formularz!')
        return render(request, self.template_name, self.get_context_data(**kwargs))


def delete_lecture_view(request, the_slug, num):
    user = request.user
    if not user.is_authenticated or user.is_student:
        return redirect('courses:courses')
    course = models.Course.objects.get(slug=the_slug)
    if course:
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
        else:
            redirect('courses:courses')
        if teacher not in course.teachers.all():
            return redirect('courses:courses')
        lecture = course.lectures.all()[num]
        lecture.delete()
        #TODO: usuwanie spotkania
        messages.info(request, 'Pomyślnie usunięto wykład!')
    return redirect('courses:courses-edit', the_slug=course.slug)


def lecture_add_file(request, pk):
    user = request.user
    if not user.is_authenticated or user.is_student:
        return redirect('courses:courses')
    lecture = models.Lecture.objects.get(pk=pk)
    if lecture:
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
        else:
            redirect('courses:courses')
        if teacher not in lecture.course.teachers.all():
            return redirect('courses:courses')

        if request.method == 'GET':
            return render(request, 'courses/lecture-file.html', {'lecture': lecture, 'form': forms.CourseFileForm})

        form = forms.CourseFileForm(request.POST, request.FILES)

        name = form.data.get('filename')
        description = form.data.get('description')
        file = request.FILES.get('file')

        if name and file:
            course_file = models.CourseFile.objects.create(
                name=name, file=file, description=description
            )
            lecture.files.add(course_file)
            lecture.save()
            messages.info(request, 'Pomyślnie dodano plik!')
        else:
            messages.error(request, 'Spróbuj ponownie!')
            return render(request, 'courses/lecture-file.html', {'lecture': lecture, 'form': forms.CourseFileForm})
    return redirect('courses:lectures-edit', pk=lecture.pk)


def delete_lecture_file(request, pk, num):
    user = request.user
    if not user.is_authenticated or user.is_student:
        return redirect('courses:courses')
    lecture = models.Lecture.objects.get(pk=pk)
    if lecture:
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
        else:
            redirect('courses:courses')
        if teacher not in lecture.course.teachers.all():
            return redirect('courses:courses')

        file = lecture.files.all()[num]
        file.delete()
        lecture.save()
        messages.info(request, 'Pomyślnie usunięto plik!')
    return redirect('courses:lectures-edit', pk=lecture.pk)
