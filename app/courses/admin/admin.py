from django.contrib import admin

from courses import models


@admin.register(models.Grade)
class GradeAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Course)
class CourseAdmin(admin.ModelAdmin):
    pass
