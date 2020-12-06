import datetime
import os
import uuid
from typing import Any

from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

PROFILE_CHOICES = (
    ('CS', 'Computer Science',),
    ('IS', 'Intelligent Systems')
)

LANGUAGE_CHOICES = (
    ('EN', 'English',),
    ('PL', 'Polish',),
)


def get_file_path(instance: Any, filename: str) -> str:
    today = datetime.date.today().strftime("%Y-%m-%d")
    return os.path.join(settings.UPLOAD_FILES_DIR, today, str(uuid.uuid4()) + filename)


class CourseFile(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to=get_file_path, verbose_name=_('File'))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at', '-updated_at',)
        verbose_name = _('File')
        verbose_name_plural = _('Files')

    def __str__(self):
        return f"{self.name} - {self.filename}"

    @property
    def filename(self) -> str:
        return self.file.name.split('/')[-1]


class Grade(models.Model):
    name = models.CharField(max_length=50, verbose_name=_('Grade\'s name'))
    start_year = models.DateField(verbose_name=_('Grade start year'))
    students = models.ManyToManyField(
        to='users.Student',
        related_name='grades',
        verbose_name=_('Students'),
    )
    supervisor = models.ForeignKey(
        to='users.Student',
        related_name='supervised_grades',
        on_delete=models.CASCADE,
        null=True, blank=True,
        verbose_name=_('Supervisor')
    )
    max_number_of_students = models.IntegerField(default=120, help_text=_('Maximum number of student at Grade'))
    profile = models.CharField(max_length=20, choices=PROFILE_CHOICES)

    class Meta:
        unique_together = ('name', 'start_year',)
        ordering = ('name', 'start_year',)
        verbose_name = _('Grade')
        verbose_name_plural = _('Grades')

    def __str__(self) -> str:
        return 'Grade: {} ({} - {})'.format(self.name, self.start_year.year, self.finish_year.year)

    @property
    def finish_year(self) -> datetime.date:
        return self.start_year + datetime.timedelta(days=365 * 3)


class Course(models.Model):
    name = models.CharField(max_length=50, verbose_name=_('Course\'s name'))
    description = models.TextField(null=True, blank=True)
    head_teacher = models.ForeignKey(
        to='users.Teacher',
        on_delete=models.CASCADE,
        related_name='courses_running',
        verbose_name=_('Head teacher')
    )
    teachers = models.ManyToManyField(
        to='users.Teacher',
        related_name='courses_teaching',
        verbose_name=_('Teachers')
    )
    grade = models.ForeignKey(
        to='courses.Grade',
        on_delete=models.CASCADE,
        related_name='courses',
    )
    ects = models.IntegerField(default=1, validators=[
        validators.MinValueValidator(0), validators.MaxValueValidator(30)
    ])
    code_meu = models.CharField(max_length=30, verbose_name=_('MEU Code'))
    has_exam = models.BooleanField(default=False)
    semester = models.IntegerField(validators=[validators.MinValueValidator(1)])
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    site = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('WWW site'))

    lecture_hours = models.IntegerField(validators=[validators.MinValueValidator(0)])
    labs_hours = models.IntegerField(validators=[validators.MinValueValidator(0)])

    files = models.ManyToManyField(CourseFile, blank=True)
    slug = models.SlugField(blank=True, null=True, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')

    def __str__(self) -> str:
        return 'Course: {}'.format(self.name)

    def clean(self):
        if not self.head_teacher.role == 'teacher':
            raise ValidationError(_('Head teacher must have teacher role'))
        super().clean()

    def save(self, *args, **kwargs):
        if not self.slug:
            uid = str(uuid.uuid4())[:20]
            year = datetime.date.today().year
            self.slug = slugify(f"{self.name}-{year}-{uid}")
        super().save(*args, **kwargs)


class CourseLectureSection(models.Model):
    name = models.CharField(max_length=20, verbose_name=_('Course lecture\'s name'))
    description = models.TextField(null=True, blank=True)


class CourseGroup(models.Model):
    name = models.CharField(max_length=20, verbose_name=_('Course group\'s name'))
    description = models.TextField(null=True, blank=True)
    course = models.ForeignKey(
        to=Course,
        on_delete=models.CASCADE,
        related_name='course'
    )
    teacher = models.ForeignKey(
        to='users.Teacher',
        on_delete=models.CASCADE,
        related_name='groups_teaching'
    )
    # WARNING: take care of handling only students from corresponding grade / validate form
    students = models.ManyToManyField(
        to='users.Student',
        verbose_name=_('Students'),
        related_name='students_groups'
    )
    files = models.ManyToManyField(CourseFile, blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = _('Course Group')
        verbose_name_plural = _('Course Groups')

    def __str__(self) -> str:
        return 'Course Group: {} - {}'.format(self.course.name, self.name)
