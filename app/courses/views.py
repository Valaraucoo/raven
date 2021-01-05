import datetime
from typing import List

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.views.generic.detail import DetailView

from courses import forms, models, tasks
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
        labs = self.object.laboratories.all().order_by('date')
        if self.request.user.is_teacher:
            context['available_labs'] = [lab for lab in labs if lab.is_available]
        else:
            user = self.request.user
            student = users_models.Student.objects.get(pk=user.pk)
            course = self.get_object()
            if student in course.students_without_groups:
                context['available_labs'] = []
            else:
                student_group = models.CourseGroup.objects.filter(
                    course=course, students__email__contains=student.email
                ).first()
                context['available_labs'] = [lab for lab in labs if (lab.is_available and student_group == lab.group)]
        context['student_without_groups_emails'] = [student.email for student in self.object.students_without_groups]
        return context


class CourseGroupJoinListView(CoursesDetailView):
    template_name = 'courses/courses-group-join.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = self.object.groups.all()
        return context


def course_group_create_view(request, the_slug):
    user = request.user
    course = models.Course.objects.get(slug=the_slug)
    if not course:
        return redirect('courses:courses')
    if not user.is_authenticated or user.is_student:
        return redirect('courses:courses')
    if user.is_teacher:
        teacher = users_models.Teacher.objects.get(email=user.email)
        if teacher not in course.teachers.all():
            return redirect('courses:courses')

    form = forms.CourseGroupModelForm(request.POST)
    form.fields['students'].queryset = course.grade.students.all()
    if request.method == 'POST':
        form = forms.CourseGroupModelForm(request.POST)
        if form.is_valid():
            group = models.CourseGroup.objects.create(
                name=form.data.get('name'),
                course=course)
            messages.info(request, 'Pomyslnie utworzono nową grupę.')
            return redirect('courses:group-edit', pk=group.pk)
        else:
            messages.error(request, 'Spróbuj ponownie.')
    return render(request, 'courses/groups/group-create.html', {'form': form, 'course': course})


def course_group_delete_view(request, the_slug, num):
    user = request.user
    course = models.Course.objects.get(slug=the_slug)
    group = course.groups.all()[num]
    if not group or not course:
        return redirect('courses:courses')
    if not user.is_authenticated or user.is_student:
        return redirect('courses:courses')
    if user.is_teacher:
        teacher = users_models.Teacher.objects.get(email=user.email)
        if teacher not in group.course.teachers.all():
            return redirect('courses:courses')
    group.delete()
    messages.info(request, 'Pomyślnie usunięto grupe.')
    return redirect('courses:group', the_slug=the_slug)


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
        context['laboratories'] = self.object.laboratories.all()
        return context

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().teachers.all():
                return redirect('courses:courses')
        if user.is_student:
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


class CourseGroupEditView(DetailView):
    template_name = 'courses/groups/group-edit.html'
    model = models.CourseGroup

    def get_context_data(self, **kwargs):
        group = self.get_object()
        form = forms.CourseGroupModelForm(initial={
            'name': group.name,
            'students': group.students.all(),
        })
        form.fields['students'].queryset = group.course.grade.students.all() | group.course.additional_students.all()
        context = {
            'group': group,
            'form': form
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
        group = self.get_object()
        form = forms.CourseGroupModelForm(request.POST)
        if form.is_valid():
            group.name = form.cleaned_data.get('name')
            for student in group.students.all():
                group.students.remove(student)
            for student in form.cleaned_data.get('students'):
                group.students.add(student)
            group.save()
            messages.info(request, 'Pomyslnie zaktualizowano grupę.')
        else:
            messages.error(request, 'Spróbuj ponownie.')
        return super().get(request, *args, **kwargs)


class LectureDetailView(LoginRequiredMixin, DetailView):
    template_name = 'courses/lectures/lecture-detail.html'
    model = models.Lecture
    context_object_name = 'lecture'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        previous_lecture = obj.course.lectures.filter(date__lt=obj.date).last()
        context['previous_lecture'] = previous_lecture
        return context

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
    template_name = 'courses/laboratories/laboratory-detail.html'
    model = models.Laboratory
    context_object_name = 'laboratory'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        previous_lab = obj.course.laboratories.filter(date__lt=obj.date, group=obj.group).last()
        context['previous_lab'] = previous_lab
        return context

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
            if student not in self.get_object().group.students.all():
                return redirect('courses:courses')
        return super().get(request, *args, **kwargs)


class LaboratoryEditView(LoginRequiredMixin, DetailView):
    template_name = 'courses/laboratories/laboratory-edit.html'
    model = models.Laboratory
    context_object_name = 'laboratory'

    def get_context_data(self, **kwargs):
        laboratory = self.get_object()
        form = forms.LaboratoryCreateForm(initial={
            'title': laboratory.title,
            'date': laboratory.date.strftime('%d.%m.%Y'),
            'time': laboratory.date.strftime('%H:%M'),
            'duration': laboratory.duration.seconds // 60,
            'description': laboratory.description,
            'show': laboratory.show,
            'meeting': laboratory.create_event,
            'group': laboratory.group,
        })
        form.fields['group'].queryset = models.CourseGroup.objects.filter(course=laboratory.course)
        context = {
            'laboratory': laboratory,
            'form': form
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
        form = forms.LaboratoryCreateForm(request.POST)

        if form.is_valid():
            title = form.data.get('title')
            date = form.data.get('date')
            time = form.data.get('time')
            duration = form.data.get('duration')
            localization = request.POST.get('localization', 'Remote')
            description = form.data.get('description', '')
            show = form.data.get('show', False)
            meeting = form.data.get('meeting', False)
            group_pk = form.data.get('group')

            if not group_pk:
                messages.error(request, 'Wybierz grupę!')
                return render(request, self.template_name, self.get_context_data(**kwargs))
            group = get_object_or_404(models.CourseGroup, pk=group_pk)

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

            if title and date_parsed and time_parsed and duration and localization and group:
                laboratory = context['laboratory']
                laboratory.title = title
                laboratory.date = date_parsed + datetime.timedelta(hours=time_parsed.hour, minutes=time_parsed.minute)
                laboratory.duration = duration
                laboratory.location = localization
                laboratory.description = description
                laboratory.show = show == 'on'
                laboratory.create_event = meeting == 'on'
                laboratory.group = group
                laboratory.save()

                # TODO: tworzenie wydarzenia w Google Calendar
                messages.info(request, 'Pomyślnie utworzono nowe laboratorium!')
                return redirect('courses:laboratory-edit', pk=laboratory.pk)
            else:
                messages.error(request, 'Uzupełnij poprawnie formularz!')
        else:
            messages.error(request, 'Uzupełnij poprawnie formularz!')
        return render(request, self.template_name, context)


class LectureEditView(LoginRequiredMixin, DetailView):
    template_name = 'courses/lectures/lecture-edit.html'
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

                # TODO: update wydarzenia w Google Calendar
                lecture.save()
                messages.info(request, 'Pomyślnie zaktualizowano wykład!')
                return redirect('courses:lectures-edit', pk=lecture.pk)
            else:
                messages.error(request, 'Uzupełnij poprawnie formularz!')
        else:
            messages.error(request, 'Uzupełnij poprawnie formularz!')
        return render(request, self.template_name, context)


class LaboratoryCreateView(LoginRequiredMixin, DetailView):
    template_name = 'courses/laboratories/laboratory-create.html'
    model = models.Course
    slug_field = 'slug'
    slug_url_kwarg = 'the_slug'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        course = self.get_object()

        form = forms.LaboratoryCreateForm()
        form.fields['group'].queryset = models.CourseGroup.objects.filter(course=course)

        return {
            'course': course,
            'form': form
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

        form = forms.LaboratoryCreateForm(request.POST)

        if form.is_valid():
            title = form.data.get('title')
            date = form.data.get('date')
            time = form.data.get('time')
            duration = form.data.get('duration')
            localization = request.POST.get('localization', 'Remote')
            description = form.data.get('description', '')
            show = form.data.get('show', False)
            meeting = form.data.get('meeting', False)
            group_pk = form.data.get('group')

            if not group_pk:
                messages.error(request, 'Wybierz grupę!')
                return render(request, self.template_name, self.get_context_data(**kwargs))
            group = get_object_or_404(models.CourseGroup, pk=group_pk)

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

            if title and date_parsed and time_parsed and duration and localization and group:
                laboratory = models.Laboratory.objects.create(
                    course=self.get_object(),
                    group=group,
                    title=title,
                    location=localization,
                    description=description,
                    date=date_parsed + datetime.timedelta(hours=time_parsed.hour, minutes=time_parsed.minute),
                    duration=duration,
                    show=show == 'on',
                    create_event=meeting == 'on',
                )
                # TODO: tworzenie wydarzenia w Google Calendar
                messages.info(request, 'Pomyślnie utworzono nowe laboratorium!')
                return redirect('courses:laboratory-detail', pk=laboratory.pk)
            else:
                messages.error(request, 'Uzupełnij poprawnie formularz!')
        else:
            messages.error(request, 'Uzupełnij poprawnie formularz!')
        return render(request, self.template_name, self.get_context_data(**kwargs))


class LectureCreateView(LoginRequiredMixin, DetailView):
    template_name = 'courses/lectures/lecture-create.html'
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
                # TODO: tworzenie wydarzenia w Google Calendar
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
        # TODO: usuwanie spotkania
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
            return render(request, 'courses/lectures/lecture-file.html', {'lecture': lecture,
                                                                          'form': forms.CourseFileForm})

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
            return render(request, 'courses/lectures/lecture-file.html', {'lecture': lecture,
                                                                          'form': forms.CourseFileForm})
    return redirect('courses:lectures-edit', pk=lecture.pk)


def laboratory_add_file(request, pk):
    user = request.user
    if not user.is_authenticated or user.is_student:
        return redirect('courses:courses')
    laboratory = models.Laboratory.objects.get(pk=pk)
    if laboratory:
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
        else:
            redirect('courses:courses')
        if teacher not in laboratory.course.teachers.all():
            return redirect('courses:courses')

        if request.method == 'GET':
            return render(request, 'courses/laboratories/laboratory-file.html',
                          {'laboratory': laboratory, 'form': forms.CourseFileForm})

        form = forms.CourseFileForm(request.POST, request.FILES)

        name = form.data.get('filename')
        description = form.data.get('description')
        file = request.FILES.get('file')

        if name and file:
            course_file = models.CourseFile.objects.create(
                name=name, file=file, description=description
            )
            laboratory.files.add(course_file)
            laboratory.save()
            messages.info(request, 'Pomyślnie dodano plik!')
        else:
            messages.error(request, 'Spróbuj ponownie!')
            return render(request, 'courses/laboratories/laboratory-file.html',
                          {'laboratory': laboratory, 'form': forms.CourseFileForm})
    return redirect('courses:laboratory-edit', pk=laboratory.pk)


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


def delete_laboratory_file(request, pk, num):
    user = request.user
    if not user.is_authenticated or user.is_student:
        return redirect('courses:courses')
    laboratory = models.Laboratory.objects.get(pk=pk)
    if laboratory:
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
        else:
            redirect('courses:courses')
        if teacher not in laboratory.course.teachers.all():
            return redirect('courses:courses')

        file = laboratory.files.all()[num]
        file.delete()
        laboratory.save()
        messages.info(request, 'Pomyślnie usunięto plik!')
    return redirect('courses:laboratory-edit', pk=laboratory.pk)


class CourseNoticeView(LoginRequiredMixin, DetailView):
    template_name = "courses/notices/notices.html"
    model = models.Course
    slug_field = 'slug'
    slug_url_kwarg = 'the_slug'
    context_object_name = 'course'
    form_class = forms.CourseNoticeModelForm

    def get_context_data(self, **kwargs):
        course = self.get_object()
        notices = course.notices.all()
        return {
            'course': course,
            'notices': notices,
            'form': self.get_form_class()
        }

    def get_form_class(self, **kwargs):
        return self.form_class(**kwargs)

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect('courses:courses')
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().teachers.all():
                return redirect('courses:courses')
        if user.is_student:
            student = users_models.Student.objects.get(email=user.email)
            if student not in self.get_object().grade.students.all():
                return redirect('courses:courses')

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return redirect('courses:courses')
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().teachers.all():
                return redirect('courses:courses')
        if user.is_student:
            return super().get(request, *args, **kwargs)

        form = self.form_class(request.POST)

        if form.is_valid():
            notice = form.save(commit=False)
            notice.sender = users_models.Teacher.objects.get(email=user.email)
            notice.course = self.get_object()
            notice.save()
            for student in notice.not_viewed.all():
                notice.not_viewed.remove(student)
            for student in self.get_object().grade.students.all():
                notice.not_viewed.add(student)
            notice.save()
            messages.info(request, 'Pomyślnie utworzono nowe ogłoszenie!')

            students_emails = [student.email for student in notice.course.grade.students.all()]
            tasks.send_new_notice_notification_email(notice, bcc=[], email_to=students_emails)
        else:
            messages.error(request, 'Spróbuj ponownie!')
        return super().get(request, *args, **kwargs)


class MyCourseMarksView(LoginRequiredMixin, DetailView):
    template_name = "courses/marks/my-marks.html"
    model = models.Course
    slug_field = 'slug'
    slug_url_kwarg = 'the_slug'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['final_mark'] = models.FinalCourseMark.objects.filter(student__email=self.request.user.email,
                                                                      course=self.get_object()).first()
        context['marks'] = models.CourseMark.objects.filter(student__email=self.request.user.email,
                                                            course=self.get_object())
        return context

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
            return redirect('courses:courses-marks', the_slug=self.kwargs.get('the_slug'))
        return super().get(request, *args, **kwargs)


class CourseMarksView(LoginRequiredMixin, DetailView):
    template_name = "courses/marks/partial-marks.html"
    model = models.Course
    slug_field = 'slug'
    slug_url_kwarg = 'the_slug'
    context_object_name = 'course'
    form_class = forms.CourseMarkModelForm

    def get_form_class(self, **kwargs):
        return self.form_class()

    def get_context_data(self, **kwargs):
        context = {
            'form': self.get_form_class(**kwargs),
            'course': self.get_object(),
        }
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(models.Course, slug=self.kwargs.get(self.slug_url_kwarg))

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_student:
            return redirect('courses:courses')
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().teachers.all():
                return redirect('courses:courses')
        context = self.get_context_data(**kwargs)
        marks = self.get_object().marks.all()

        if request.GET.get('student'):
            name_partial = request.GET.get('student').split(' ')
            if len(name_partial) == 1:
                marks = marks.filter(student__first_name__contains=name_partial[0])
            if len(name_partial) == 2:
                marks = marks.filter(student__first_name__contains=name_partial[0])
                marks = marks.filter(student__last_name__contains=name_partial[1])
            if len(name_partial) > 2:
                marks = marks.filter(student__first_name__contains=name_partial[0])
                marks = marks.filter(student__last_name__contains=name_partial[1])
        context['marks'] = marks
        context['student'] = request.GET.get('student', '')
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = request.user
        if user.is_student:
            return redirect('courses:courses')
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().teachers.all():
                return redirect('courses:courses')

        form = self.form_class(request.POST)
        email = request.POST.get('email')
        if form.is_valid() and email:
            try:
                student = users_models.Student.objects.get(email=email)
            except Exception:
                messages.error(request, 'Nie znaleziono studenta!')
                return super().get(request, *args, **kwargs)
            if student and student in self.get_object().grade.students.all():
                mark = form.save(commit=False)
                mark.teacher = users_models.Teacher.objects.get(email=user.email)
                mark.course = self.get_object()
                mark.student = student
                mark.save()
                messages.info(request, 'Pomyslnie dodano ocenę!')
            else:
                messages.error(request, 'Nie znaleziono studenta!')
        return self.get(request, *args, **kwargs)


class TotalCourseMarkView(LoginRequiredMixin, DetailView):
    template_name = "courses/marks/total-marks.html"
    model = models.Course
    slug_field = 'slug'
    slug_url_kwarg = 'the_slug'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = {
            'course': self.get_object(),
        }
        return context

    def get_object(self, queryset=None):
        return get_object_or_404(models.Course, slug=self.kwargs.get(self.slug_url_kwarg))

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_student:
            return redirect('courses:courses')
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().teachers.all():
                return redirect('courses:courses')
        context = self.get_context_data(**kwargs)
        students = self.get_object().grade.students.all()

        if request.GET.get('student'):
            name_partial = request.GET.get('student').split(' ')
            if len(name_partial) == 1:
                students = students.filter(first_name__contains=name_partial[0])
            if len(name_partial) == 2:
                students = students.filter(first_name__contains=name_partial[0])
                students = students.filter(last_name__contains=name_partial[1])
            if len(name_partial) > 2:
                students = students.filter(first_name__contains=name_partial[0])
                students = students.filter(last_name__contains=name_partial[1])

        context['students'] = students
        context['student'] = request.GET.get('student', '')
        return render(request, self.template_name, context)


class CourseMarkEditView(LoginRequiredMixin, DetailView):
    template_name = "courses/marks/mark-edit.html"
    model = models.CourseMark
    context_object_name = 'mark'
    form_class = forms.CourseMarkModelForm

    def get_context_data(self, **kwargs):
        mark = self.get_object()
        course = mark.course
        form = self.form_class(initial={
            'mark': mark.mark,
            'description': mark.description
        })
        context = {
            'form': form,
            'course': course
        }
        return context

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_student:
            student = users_models.Student.objects.get(email=user.email)
            if student not in self.get_object().course.grade.students.all():
                return redirect('courses:courses')
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().course.teachers.all():
                return redirect('courses:courses')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        user = request.user
        if user.is_student:
            student = users_models.Student.objects.get(email=user.email)
            if student not in self.get_object().course.grade.students.all():
                return redirect('courses:courses')
        if user.is_teacher:
            teacher = users_models.Teacher.objects.get(email=user.email)
            if teacher not in self.get_object().course.teachers.all():
                return redirect('courses:courses')

        form = self.form_class(request.POST)
        if form.is_valid():
            mark = form.cleaned_data.get('mark')
            description = form.cleaned_data.get('description')
            obj = self.get_object()
            obj.mark = mark
            obj.description = description
            obj.save()
            messages.info(request, 'Pomyślnie zapisano zmiany!')
        else:
            messages.error(request, 'Spróbuj ponownie!')
        return super().get(request, *args, **kwargs)


def delete_course_mark(request, the_slug, num):
    user = request.user
    if user.is_student or not user.is_authenticated:
        return redirect('courses:courses')
    try:
        course = models.Course.objects.get(slug=the_slug)
    except Exception:
        return redirect('courses:courses')
    if user.is_teacher:
        teacher = users_models.Teacher.objects.get(email=user.email)
        if teacher not in course.teachers.all():
            return redirect('courses:courses')

    mark = course.marks.all()[num]
    mark.delete()
    course.save()
    messages.info(request, 'Pomyślnie usunięto ocenę!')
    return redirect('courses:courses-marks', the_slug=course.slug)


def set_final_course_mark_view(request, the_slug, pk):
    user = request.user
    if user.is_student or not user.is_authenticated:
        return redirect('courses:courses')
    try:
        course = models.Course.objects.get(slug=the_slug)
    except Exception:
        return redirect('courses:courses')
    if user.is_teacher:
        teacher = users_models.Teacher.objects.get(email=user.email)
        if teacher not in course.teachers.all():
            return redirect('courses:courses')

    try:
        student = users_models.Student.objects.get(pk=pk)
    except Exception:
        return redirect('courses:courses-total-marks', the_slug=the_slug)
    form = forms.CourseSetFinalMarkModelForm()

    if request.method == 'POST':
        form = forms.CourseSetFinalMarkModelForm(request.POST)
        if form.is_valid():
            mark = form.save(commit=False)
            mark.course = course
            mark.teacher = users_models.Teacher.objects.get(email=user.email)
            mark.student = student
            mark.save()
            messages.info(request, 'Pomyślnie wystawiono ocenę!')
            return redirect('courses:courses-total-marks', the_slug=the_slug)
        else:
            messages.error(request, 'Spróbuj ponownie!')

    template_name = "courses/marks/set-final-mark.html"
    context = {
        'student': student,
        'course': course,
        'form': form
    }
    return render(request, template_name, context)


def edit_final_course_mark_view(request, the_slug, pk):
    user = request.user
    if user.is_student or not user.is_authenticated:
        return redirect('courses:courses')
    try:
        course = models.Course.objects.get(slug=the_slug)
    except Exception:
        return redirect('courses:courses')
    if user.is_teacher:
        teacher = users_models.Teacher.objects.get(email=user.email)
        if teacher not in course.teachers.all():
            return redirect('courses:courses')

    try:
        student = users_models.Student.objects.get(pk=pk)
    except Exception:
        return redirect('courses:courses-total-marks', the_slug=the_slug)

    mark = student.courses_final_marks.filter(course=course).first()
    form = forms.CourseSetFinalMarkModelForm(instance=mark)

    if request.method == 'POST':
        form = forms.CourseSetFinalMarkModelForm(data=request.POST, instance=mark)
        if form.is_valid():
            mark = form.save(commit=False)
            mark.teacher = users_models.Teacher.objects.get(email=user.email)
            mark.save()
            messages.info(request, 'Pomyślnie zaktualizowano ocenę!')
            return redirect('courses:courses-total-marks', the_slug=the_slug)
        else:
            messages.error(request, 'Spróbuj ponownie!')

    template_name = "courses/marks/edit-final-mark.html"
    context = {
        'student': student,
        'course': course,
        'form': form
    }
    return render(request, template_name, context)


class AssignmentCreateView(LoginRequiredMixin, DetailView):
    template_name = "courses/assignments/create.html"
    model = models.Laboratory
    context_object_name = 'laboratory'
    form_class = forms.AssignmentCreateModelForm

    def get_context_data(self, **kwargs):
        laboratory = self.get_object()
        form = self.form_class()
        context = {
            'form': form,
            'laboratory': laboratory
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

        form = self.form_class(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.laboratory = self.get_object()
            assignment.teacher = users_models.Teacher.objects.get(email=user.email)
            assignment.save()
            messages.info(request, 'Pomyslnie dodano nowe zadanie!')
            tasks.send_new_assignment_notification_email(assignment, [], [
                student.email for student in self.get_object().group.students.all()
            ])
            return redirect('courses:laboratory-detail', pk=self.get_object().pk)
        else:
            messages.error(request, 'Sprobuj ponownie!')
        return super().get(request, *args, **kwargs)


def delete_assignment_view(request, pk, num):
    user = request.user
    if not user.is_authenticated or user.is_student:
        return redirect('courses:courses')

    lab = models.Laboratory.objects.filter(pk=pk).first()
    if not lab:
        return redirect('courses:courses')
    if user.is_teacher:
        teacher = users_models.Teacher.objects.get(email=user.email)
        if teacher not in lab.course.teachers.all():
            return redirect('courses:courses')

    assignment = lab.assignments.all()[num]
    assignment.delete()
    lab.save()
    messages.info(request, 'Pomyslnie usunieto zadanie!')
    return redirect('courses:laboratory-detail', pk=lab.pk)
