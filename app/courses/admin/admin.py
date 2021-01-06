import typing

from django.contrib import admin
from django.shortcuts import reverse
from django.utils.html import format_html

from courses import models

from .filters import CourseStartYearFiler


@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    """
    GradeAdmin is customized admin.ModelAdmin class
    """
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
    """
    CourseAdmin is customized admin.ModelAdmin class
    """
    autocomplete_fields = ('head_teacher', 'grade')
    filter_horizontal = ('teachers', 'additional_students')
    search_fields = ('name', 'head_teacher__last_name', 'head_teacher__first_name', 'code_meu',)
    list_display = ('name', 'head_teacher', 'language', 'code_meu', 'semester', 'has_exam')
    list_filter = ('has_exam', 'semester', 'language')


@admin.register(models.CourseFile)
class CourseFileAdmin(admin.ModelAdmin):
    """
    CourseFileAdmin is customized admin.ModelAdmin class
    """
    list_display = ('name',)
    search_fields = ('name',)


class EventAdminBase(admin.ModelAdmin):
    """
    EventAdminBase is customized admin.ModelAdmin class
    """
    search_fields = ('title',)
    list_display = ('title', 'date', 'location', 'duration', 'is_available', 'was_held')
    list_filter = ('date', 'location',)
    filter_horizontal = ('files',)

    readonly_fields = ('is_available', 'was_held',)

    def is_available(self, obj: models.Laboratory) -> bool:
        return obj.is_available
    is_available.boolean = True

    def was_held(self, obj: models.Laboratory) -> bool:
        return obj.was_held
    was_held.boolean = True


@admin.register(models.Lecture)
class LectureAdmin(EventAdminBase):
    """
    LectureAdmin is customized admin.ModelAdmin class
    """
    autocomplete_fields = ('course',)
    fieldsets = (
        (None, {
            'fields': ('title', 'location', 'course', 'description', 'date', 'duration', 'files', 'reminders'),
        }),
        ('Event', {
            'fields': ('create_event', 'event_id', 'meeting_link', 'hangout_link'),
            'classes': ('collapse', 'open'),
        })
    )


@admin.register(models.Laboratory)
class LaboratoryAdmin(EventAdminBase):
    """
    LaboratoryAdmin is customized admin.ModelAdmin class
    """
    autocomplete_fields = ('course', 'group',)
    fieldsets = (
        (None, {
            'fields': ('title', 'location', 'course', 'group',
                       'description', 'date', 'duration', 'files', 'reminders'),
        }),
        ('Event', {
            'fields': ('create_event', 'event_id', 'meeting_link', 'hangout_link'),
            'classes': ('collapse', 'open'),
        })
    )


class CourseMarkBase(admin.ModelAdmin):
    """
    CourseMarkBase is customized admin.ModelAdmin class
    """
    fields = ('course', 'student', 'mark', 'description', 'teacher',)
    autocomplete_fields = ('course', 'student', 'teacher',)
    list_display = ('course', 'student', 'teacher', 'mark', 'mark_decimal',)
    list_filter = ('course',)
    search_fields = ('student__first_name', 'student__last_name')

    readonly_fields = ('mark_decimal',)

    def mark_decimal(self, obj: models.CourseMark) -> float:
        return obj.mark_decimal


@admin.register(models.CourseMark)
class CourseMarkAdmin(CourseMarkBase):
    """
    CourseMarkAdmin is customized admin.ModelAdmin class
    """
    pass


@admin.register(models.FinalCourseMark)
class FinalCourseMarkAdmin(CourseMarkBase):
    """
    FinalCourseMarkAdmin is customized admin.ModelAdmin class
    """
    pass


@admin.register(models.CourseGroup)
class GroupAdmin(admin.ModelAdmin):
    """
    GroupAdmin is customized admin.ModelAdmin class
    """
    search_fields = ('name',)
    autocomplete_fields = ('course',)
    filter_horizontal = ('students',)
    list_display = ('name', 'course_link', 'students_count')

    readonly_fields = ('course_link', 'students_count',)

    def course_link(self, obj: models.CourseGroup):
        href = reverse('admin:courses_course_change', args=(obj.course.pk,))
        return format_html(f'<a href="{href}">{obj.course.name}</a>')

    def students_count(self, obj: models.CourseGroup) -> int:
        return obj.students_count


@admin.register(models.Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    """
    AssignmentAdmin is customized admin.ModelAdmin class
    """
    autocomplete_fields = ('teacher', 'laboratory',)
    list_display = ('title', 'deadline', 'laboratory_link', 'is_actual')
    list_filter = ('deadline',)
    search_fields = ('laboratory__title', 'title',)

    readonly_fields = ('laboratory_link', 'is_actual')

    def laboratory_link(self, obj: models.Assignment):
        href = reverse("admin:courses_laboratory_change", args=(obj.laboratory.pk,))
        return format_html(f'<a href="{href}">{obj.laboratory.title}</a>')

    def is_actual(self, obj: models.Assignment):
        return obj.is_actual
    is_actual.boolean = True


@admin.register(models.CourseNotice)
class CourseNoticeAdmin(admin.ModelAdmin):
    """
    CourseNoticeAdmin is customized admin.ModelAdmin class
    """
    autocomplete_fields = ('course', 'sender')
    filter_horizontal = ('not_viewed',)
    list_display = ('course', 'title', 'sender', 'created_at',)
