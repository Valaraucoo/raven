import datetime
import os
import uuid
from typing import Any

from django.conf import settings
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from utils.meetings import meetings

PROFILE_CHOICES = (
    ('CS', _('Computer Science')),
    ('IS', _('Intelligent Systems'))
)

LANGUAGE_CHOICES = (
    ('EN', _('English')),
    ('PL', _('Polish')),
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
    additional_students = models.ManyToManyField('users.Student', 'additional_courses')

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

    @property
    def total_students(self):
        return self.grade.students.all() | self.additional_students.all()


class Event(models.Model):
    title = models.CharField(max_length=100, verbose_name=_('Lecture\'s title'))
    location = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    date = models.DateTimeField()
    duration = models.DurationField(default=datetime.timedelta(hours=1.5))
    files = models.ManyToManyField(CourseFile, blank=True)
    reminders = models.BooleanField(default=True)
    time_delta = models.DurationField(default=datetime.timedelta(days=7), null=True, blank=True)
    show = models.BooleanField(default=False)

    create_event = models.BooleanField(default=False)
    event_id = models.CharField(max_length=500, null=True, blank=True)
    meeting_link = models.CharField(max_length=500, null=True, blank=True)
    hangout_link = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        ordering = ('date',)
        abstract = True

    @property
    def is_available(self) -> bool:
        if self.show:
            return True
        if self.time_delta:
            today = timezone.now()
            return (self.date - today) < self.time_delta
        return False

    @property
    def was_held(self) -> bool:
        return self.date < timezone.now()


class Lecture(Event):
    course = models.ForeignKey('Course', related_name='lectures', on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f'Lecture: {self.title}({self.date})'

    @property
    def students(self):
        return self.course.grade.students.all()
