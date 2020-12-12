from django.contrib import admin

from courses import models


@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    autocomplete_fields = ('supervisor',)
    filter_horizontal = ('students',)
    search_fields = ('name', 'start_year',)
    list_display = ('name', 'start_year', 'profile', 'max_number_of_students',)


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


@admin.register(models.LectureMark)
class LectureMarkAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Laboratory)
class LaboratoryAdmin(admin.ModelAdmin):
    pass


@admin.register(models.CourseGroup)
class GroupAdmin(admin.ModelAdmin):
    pass


@admin.register(models.CourseNotice)
class CourseNoticeAdmin(admin.ModelAdmin):
    pass
