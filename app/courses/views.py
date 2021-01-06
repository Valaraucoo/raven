import datetime
from typing import List

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.views import generic
from django.views.generic.detail import DetailView

from core import settings
from courses import forms, models, tasks
from users import models as users_models
from utils.meetings import meetings


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
    """
    View used to handle /courses/ GET requests.

    **Context:**
    Returns the courses the user is enrolled in / or which user conducts.

    ``courses``
        An instance of :Queryset: - user's courses

    ``has_courses``
        Boolean, :True if len(courses) > 0:

    **Template:**

    :template:`courses/courses.html`
    """
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
    """
    View used to handle /courses/<slug>/ GET requests.

    **Context:**
    Returns details of the specified course.

    ``course``
        An instance of :model: `courses.Course`

    ``available_lectures``
        An instance of :Queryset: - all available lectures in specified course

    ``available_labs``
        An instance of :Queryset: - all available laboratories in specified course

    ``student_without_groups_emails``
        An instance of `users.Student` - all students without group

    **Template:**

    :template:`courses/courses-detail.html`
    """
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
    """
    View used to handle /courses/<slug:the_slug>/groups/ GET requests.

    **Context:**

    ``groups``
        An instance of :Queryset: `courses.CourseGroup`

    ``course``
        An instance of :model: `courses.Course`

    ``available_lectures``
        An instance of :Queryset: - all available lectures in specified course

    ``available_labs``
        An instance of :Queryset: - all available laboratories in specified course

    ``student_without_groups_emails``
        An instance of `users.Student` - all students without group

    **Template:**

    :template:`courses/courses-group-join.html`
    """
    template_name = 'courses/courses-group-join.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['groups'] = self.object.groups.all()
        return context


def course_group_create_view(request, the_slug):
    """
    View used to handle /courses/<slug:the_slug>/groups/create/ GET/POST requests.
    View is used to create new groups within the specified course.

    **Context:**

    ``form``
        An instance of :forms.ModelForm:

    ``course``
        An instance of :model: `courses.Course`

    **Template:**

    :template:`courses/groups/group-create.html`
    """
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
    """
    View used to handle /courses/<slug:the_slug>/groups/<int:num>/delete/ GET requests.
    View is used to delete groups within the specified course.

    **Template:**

    :template:`None`
    """
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
    """
    View used to handle /courses/<slug:the_slug>/groups/join/<int:num> GET requests.
    View is used by students to join specified group within the course.

    **Template:**

    :template:`None`
    """
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
    """
    View used to handle /courses/<slug:the_slug>/edit/ GET/POST requests.
    View is used by teachers to edit specified course.

    **Context:**

    ``course``
        An instance of :model: `courses.Course`

    ``available_lectures``
        An instance of :Queryset: - all available lectures in specified course

    ``available_labs``
        An instance of :Queryset: - all available laboratories in specified course

    ``lectures``
        An instance of :Queryset: - all lectures in specified course

    ``laboratories``
        An instance of :Queryset: - all laboratories in specified course

    ``student_without_groups_emails``
        An instance of `users.Student` - all students without group

    **Template:**

    :template:`courses/courses-detail-edit.html`
    """
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
    """
    View used to handle /courses/groups/<int:pk>/ GET/POST requests.
    View is used by teachers to edit specified group within the course.

    **Context:**

    ``group``
        An instance of :model: `courses.CourseGroup`

    ``form``
        An instance of `courses.forms.CourseGroupModelForm`

    **Template:**

    :template:`courses/groups/group-edit.html`
    """
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
    """
    View used to handle /courses/lecture/<int:pk>/detail/ GET requests.

    **Context:**

    ``lecture``
        An instance of :model: `courses.Lecture`

    ``previous_lecture``
        An instance of :model: `courses.Lecture`

    **Template:**

    :template:`courses/lectures/lecture-detail.html`
    """
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
    """
    View used to handle /courses/laboratory/<int:pk>/detail/ GET requests.

    **Context:**

    ``laboratory``
        An instance of :model: `courses.Laboratory`

    ``previous_lab``
        An instance of :model: `courses.Laboratory`

    **Template:**

    :template:`courses/laboratories/laboratory-detail.html`
    """
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
    """
    View used to handle /courses/laboratory/<int:pk>/edit/ GET/POST requests.
    Views is used by teachers to edit specified laboratory.

    **Context:**
    Returns all available groups within the course.

    ``laboratory``
        An instance of :model: `courses.Laboratory`

    ``form``
        An instance of `courses.forms.LaboratoryCreateForm`

    **Template:**

    :template:`courses/laboratories/laboratory-edit.html`
    """
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

                if laboratory.event_id and laboratory.create_event and settings.USE_GOOGLE_API:
                    meeting = meetings.update_google_calendar_event(
                        event_id=laboratory.event_id,
                        data={
                            'start': laboratory.date,
                            'end': laboratory.date + laboratory.duration,
                            'description': laboratory.description,
                            'location': laboratory.location
                        }
                    )
                    laboratory.event_id = meeting.get('id', '')
                    laboratory.hangout_link = meeting.get('hangoutLink', '')
                elif not laboratory.create_event and laboratory.event_id and settings.USE_GOOGLE_API:
                    meetings.delete_google_calendar_event(laboratory.event_id)
                    laboratory.event_id = ''
                    laboratory.hangout_link = ''
                    laboratory.save()
                    messages.info(request, 'Pomyślnie zaktualizowano laboratorium! Usunieto wydarzenie!')
                    return redirect('courses:laboratory-edit', pk=laboratory.pk)
                elif laboratory.create_event and settings.USE_GOOGLE_API:
                    meeting = meetings.create_google_calendar_event(
                        title=laboratory.title,
                        location=laboratory.location or '',
                        description=laboratory.description or '',
                        start_date=laboratory.date,
                        end_date=laboratory.date + laboratory.duration,
                        organizer_email=laboratory.course.head_teacher.email,
                        attendees=[student.email for student in laboratory.group.students.all()],
                        create_meet=True
                    )
                    laboratory.event_id = meeting.get('id', '')
                    laboratory.hangout_link = meeting.get('hangoutLink', '')
                laboratory.save()

                messages.info(request, 'Pomyślnie utworzono nowe laboratorium!')
                return redirect('courses:laboratory-edit', pk=laboratory.pk)
            else:
                messages.error(request, 'Uzupełnij poprawnie formularz!')
        else:
            messages.error(request, 'Uzupełnij poprawnie formularz!')
        return render(request, self.template_name, context)


class LectureEditView(LoginRequiredMixin, DetailView):
    """
    View used to handle /courses/lecture/<int:pk>/edit/ GET/POST requests.
    Views is used by teachers to edit specified lecture.

    **Context:**
    Returns all available groups within the course.

    ``lecture``
        An instance of :model: `courses.Lecture`

    ``form``
        An instance of `courses.forms.LectureCreateForm`

    **Template:**

    :template:`courses/lectures/lecture-edit.html`
    """
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

                lecture.save()

                if lecture.create_event and lecture.event_id and lecture.create_event and \
                        settings.USE_GOOGLE_API:
                    meeting = meetings.update_google_calendar_event(
                        event_id=lecture.event_id,
                        data={
                            'start': lecture.date,
                            'end': lecture.date + lecture.duration,
                            'description': lecture.description,
                            'location': lecture.location
                        }
                    )
                    lecture.event_id = meeting.get('id', '')
                    lecture.hangout_link = meeting.get('hangoutLink', '')
                elif not lecture.create_event and lecture.event_id and settings.USE_GOOGLE_API:
                    meetings.delete_google_calendar_event(lecture.event_id)
                    lecture.event_id = ''
                    lecture.hangout_link = ''
                    lecture.save()
                    messages.info(request, 'Pomyślnie zaktualizowano wykład! Usunieto wydarzenie!')
                    return redirect('courses:lectures-edit', pk=lecture.pk)
                elif lecture.create_event and settings.USE_GOOGLE_API:
                    meeting = meetings.create_google_calendar_event(
                        title=lecture.title,
                        location=lecture.location or '',
                        description=lecture.description or '',
                        start_date=lecture.date,
                        end_date=lecture.date + lecture.duration,
                        organizer_email=lecture.course.head_teacher.email,
                        attendees=[student.email for student in lecture.course.grade.students.all()],
                        create_meet=True
                    )
                    lecture.event_id = meeting.get('id', '')
                    lecture.hangout_link = meeting.get('hangoutLink', '')
                lecture.save()
                messages.info(request, 'Pomyślnie zaktualizowano wykład!')
                return redirect('courses:lectures-edit', pk=lecture.pk)
            else:
                messages.error(request, 'Uzupełnij poprawnie formularz!')
        else:
            messages.error(request, 'Uzupełnij poprawnie formularz!')
        return render(request, self.template_name, context)


class LaboratoryCreateView(LoginRequiredMixin, DetailView):
    """
    View used to handle /courses/<slug:the_slug>/laboratory/create/ GET/POST requests.
    Views is used by teachers to create new laboratory.

    **Context:**
    Returns all available groups within the course.

    ``course``
        An instance of :model: `courses.Course`

    ``form``
        An instance of `courses.forms.LaboratoryCreateForm`

    **Template:**

    :template:`courses/laboratories/laboratory-create.html`
    """
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
                laboratory.save()
                if laboratory.create_event and settings.USE_GOOGLE_API:
                    meeting = meetings.create_google_calendar_event(
                        title=laboratory.title,
                        location=laboratory.location or '',
                        description=laboratory.description or '',
                        start_date=laboratory.date,
                        end_date=laboratory.date + laboratory.duration,
                        organizer_email=laboratory.course.head_teacher.email,
                        attendees=[student.email for student in laboratory.group.students.all()],
                        create_meet=True
                    )
                    laboratory.event_id = meeting.get('id', '')
                    laboratory.hangout_link = meeting.get('hangoutLink', '')
                    laboratory.save()
                messages.info(request, 'Pomyślnie utworzono nowe laboratorium!')
                return redirect('courses:laboratory-detail', pk=laboratory.pk)
            else:
                messages.error(request, 'Uzupełnij poprawnie formularz!')
        else:
            messages.error(request, 'Uzupełnij poprawnie formularz!')
        return render(request, self.template_name, self.get_context_data(**kwargs))


class LectureCreateView(LoginRequiredMixin, DetailView):
    """
    View used to handle /courses/<slug:the_slug>/lecture/create/ GET/POST requests.
    Views is used by teachers to create new lecture.

    **Context:**
    Returns all available groups within the course.

    ``course``
        An instance of :model: `courses.Course`

    ``form``
        An instance of `courses.forms.LectureCreateForm`

    **Template:**

    :template:`courses/lectures/lecture-create.html`
    """
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
                lecture.save()

                if lecture.create_event and settings.USE_GOOGLE_API:
                    meeting = meetings.create_google_calendar_event(
                        title=lecture.title,
                        location=lecture.location or '',
                        description=lecture.description or '',
                        start_date=lecture.date,
                        end_date=lecture.date + lecture.duration,
                        organizer_email=lecture.course.head_teacher.email,
                        attendees=[student.email for student in lecture.course.grade.students.all()],
                        create_meet=True
                    )
                    lecture.event_id = meeting.get('id', '')
                    lecture.hangout_link = meeting.get('hangoutLink', '')
                lecture.save()

                messages.info(request, 'Pomyślnie utworzono nowy wykład!')
                return redirect('courses:lectures-detail', pk=lecture.pk)
            else:
                messages.error(request, 'Uzupełnij poprawnie formularz!')
        else:
            messages.error(request, 'Uzupełnij poprawnie formularz!')
        return render(request, self.template_name, self.get_context_data(**kwargs))


def delete_lecture_view(request, the_slug, num):
    """
    View used to handle /courses/<slug:the_slug>/delete/<int:num>/ GET requests.
    Views is used by teachers to delete specified lecture.

    **Context:**

    **Template:**

    :template:`None`
    """
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
    """
    View used to handle /courses/lecture/<int:pk>/file/add/ GET/POST requests.
    Views is used by teachers to add file to specified lecture.

    **Context:**

    ``lecture``
        An instance of `courses.Lecture`

    ``form``
        An instance of `courses.forms.CourseFileForm`

    **Template:**

    :template:`courses/lectures/lecture-file.html`
    """
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
    """
    View used to handle /courses/laboratory/<int:pk>/file/add/ GET/POST requests.
    Views is used by teachers to add file to specified laboratory.

    **Context:**

    ``laboratory``
        An instance of `courses.Labroatory`

    ``form``
        An instance of `courses.forms.CourseFileForm`

    **Template:**

    :template:`courses/laboratories/laboratory-file.html`
    """
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
    """
    View used to handle /courses/lecture/<int:pk>/file/delete/<int:num>/ GET requests.
    Views is used by teachers to delete file to specified lecture.

    **Template:**

    :template:`None`
    """
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
    """
    View used to handle /courses/laboratory/<int:pk>/file/delete/<int:num>/ GET requests.
    Views is used by teachers to delete file to specified laboratory.

    **Template:**

    :template:`None`
    """
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
    """
    View used to handle /courses/<slug:the_slug>/notices/ GET/POST requests.
    Views is used to edit and view notices.

    **Context:**

    ``course``
        An instance of `courses.Course`

    ``notices``
        An instance of `courses.CourseNotice`

    ``form``
        An instance of `courses.forms.CourseNoticeModelForm`

    **Template:**

    :template:`courses/notices/notices.html`
    """
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
    """
    View used to handle /courses/<slug:the_slug>/my-marks/ GET requests.
    Views is used by students to view theirs marks at specified course.

    **Context:**

    ``final_mark``
        An instance of `courses.FinalCourseMark`

    ``marks``
        An instance of `courses.CourseMark`

    ``course``
        An instance of `courses.Course`

    **Template:**

    :template:`courses/marks/my-marks.html`
    """
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
    """
    View used to handle /courses/<slug:the_slug>/marks/ GET/POST requests.
    Views is used to explore and edit marks at specified course.

    **Context:**

    ``form``
        An instance of `courses.forms.CourseMarkModelForm`

    ``course``
        An instance of `courses.Course`

    **Template:**

    :template:`courses/marks/partial-marks.html`
    """
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
    """
    View used to handle /courses/<slug:the_slug>/total-marks/ GET requests.
    Views is used to explore student's marks summary.

    **Context:**

    ``course``
        An instance of `courses.Course`

    **Template:**

    :template:`courses/marks/total-marks.html`
    """
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
    """
    View used to handle /courses/marks/edit/<int:pk>/ GET/POST requests.
    Views is used to edit specified mark instance.

    **Context:**

    ``mark``
        An instance of `courses.CourseMark`

    ``course``
        An instance of `courses.Course`

    ``form``
        An instance of `course.forms.CourseMarkModelForm`

    **Template:**

    :template:`courses/marks/mark-edit.html`
    """
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
    """
    View used to handle /courses/<slug:the_slug>/marks/delete/<int:num>/ GET requests.
    Views is used to delete specified mark instance.

    **Template:**

    :template:`None`
    """
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
    """
    View used to handle /courses/<slug:the_slug>/marks/final/set/<int:pk>/ GET/POST requests.
    Views is used to set final mark for specified student.

    **Context:**

    ``course``
        An instance of `courses.Course`

    ``student``
        An instance of `users.Student`

    ``form``
        An instance of `courses.forms.CourseSetFinalMarkModelForm`

    **Template:**

    :template:`courses/marks/set-final-mark.html`
    """
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
    """
    View used to handle /courses/<slug:the_slug>/marks/final/edit/<int:pk>/ GET/POST requests.
    Views is used to edit final mark for specified student.

    **Context:**

    ``course``
        An instance of `courses.Course`

    ``student``
        An instance of `users.Student`

    ``form``
        An instance of `courses.forms.CourseSetFinalMarkModelForm`

    **Template:**

    :template:`courses/marks/edit-final-mark.html`
    """
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
    """
    View used to handle /courses/laboratory/<int:pk>/assignments/add/ GET/POST requests.
    Views is used by teachers to create new assignment.

    **Context:**

    ``laboratory``
        An instance of `courses.Laboratory`

    ``student``
        An instance of `users.Student`

    ``form``
        An instance of `courses.forms.AssignmentCreateModelForm`

    **Template:**

    :template:`courses/assignments/create.html`
    """
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
    """
    View used to handle /courses/laboratory/<int:pk>/assignments/delete/<int:num>/ GET requests.
    Views is used by teachers to delete specified assignment.

    **Template:**

    :template:`None`
    """
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
