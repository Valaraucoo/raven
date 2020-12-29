import typing

from django.contrib import admin
from django.shortcuts import reverse
from django.utils.html import format_html

from courses import models

from .filters import CourseStartYearFiler


@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    autocomplete_fields = ('supervisor',)
    filter_horizontal = ('students',)
    search_fields = ('name', 'start_year',)
    list_display = ('name', 'year', 'profile', 'max_number_of_students',)
    list_filter = (CourseStartYearFiler,)
    ordering = ('start_year', 'name',)

    readonly_fields = ('courses', 'create_course', 'year')

    def get_fieldsets(self, request, obj=None):
        base_fields = ('name', 'profile', 'start_year', 'students', 'supervisor', 'max_number_of_students',)
        if not obj:
            return [
                ('Grade Info', {'fields': base_fields}),
            ]
        return [
            ('Grade Info', {'fields': base_fields}),
            ('Management', {'fields': ('courses', 'create_course',)})
        ]

    def courses(self, obj: models.Grade = None) -> str:
        if not obj.courses.all():
            return '-'
        html = ", ".join([
            f'<a href="{reverse("courses:courses-detail", args=(course.slug,))}">{course}</a>' for course in
            obj.courses.all()
        ])
        return format_html(html)
    courses.short_description = 'Available courses'

    def create_course(self, obj: models.Grade = None) -> str:
        href = reverse("admin:courses_course_add")
        return format_html(f'&nbsp;&nbsp;&nbsp;<a class="button" href="{href}">Create course</a>')
    create_course.short_description = 'Create course'

    def year(self, obj: models.Grade = None) -> typing.Optional[int]:
        if obj:
            return obj.start_year.year
    year.short_description = 'Start Year'


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    autocomplete_fields = ('head_teacher', 'grade')
    filter_horizontal = ('teachers', 'additional_students')
    search_fields = ('name', 'head_teacher__last_name', 'head_teacher__first_name', 'code_meu',)
    list_display = ('name', 'head_teacher', 'language', 'code_meu', 'semester', 'has_exam')
    list_filter = ('has_exam', 'semester', 'language')


@admin.register(models.CourseFile)
class CourseFileAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(models.Lecture)
class LectureAdmin(admin.ModelAdmin):
    autocomplete_fields = ('course',)
    filter_horizontal = ('files',)
    list_display = ('title', 'date', 'location', 'duration',)
    search_fields = ('title', 'location', 'course__head_teacher')
    list_filter = ('location',)


@admin.register(models.Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.CourseMark)
class CourseMarkAdmin(admin.ModelAdmin):
    pass


@admin.register(models.FinalCourseMark)
class FinalCourseMarkAdmin(admin.ModelAdmin):
    pass


@admin.register(models.CourseGroup)
class GroupAdmin(admin.ModelAdmin):
    pass


@admin.register(models.CourseNotice)
class CourseNoticeAdmin(admin.ModelAdmin):
    autocomplete_fields = ('course', 'sender')
    filter_horizontal = ('not_viewed',)
    list_display = ('course', 'title', 'sender', 'created_at',)
