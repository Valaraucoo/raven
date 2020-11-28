from typing import List

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render, get_object_or_404
from django.views import generic
from django.views.generic.detail import DetailView

from courses import models
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
        return context


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


class LectureEditView(CoursesDetailView):
    pass