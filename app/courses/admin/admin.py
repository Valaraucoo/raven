from django.contrib import admin

from courses import models


@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    pass


@admin.register(models.CourseFile)
class CourseFileAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Lecture)
class LectureAdmin(admin.ModelAdmin):
    pass


@admin.register(models.LectureMark)
class LectureMarkAdmin(admin.ModelAdmin):
    pass
