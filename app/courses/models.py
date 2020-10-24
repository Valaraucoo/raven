import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

PROFILE_CHOICES = (
    ('CS', 'Computer Science',),
)

LANGUAGE_CHOICES = (
    ('EN', 'English',),
    ('PL', 'Polish',),
)


class Grade(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name=_('Grade\'s name')
    )
    start_year = models.DateField(verbose_name=_('Grade start year'))
    students = models.ManyToManyField(
        to='users.User',
        related_name='grades',
        verbose_name=_('Students'),
    )
    supervisor = models.ForeignKey(
        to='users.User',
        related_name='supervised_grades',
        on_delete=models.CASCADE,
        verbose_name=_('Supervisor')
    )
    max_number_of_students = models.IntegerField(
        default=120,
        help_text=_('Maximum number of student at Grade')
    )
    profile = models.CharField(
        max_length=20,
        choices=PROFILE_CHOICES
    )

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

    def clean(self):
        super().clean()
        # TODO:
        # for student in self.students.all():
        #     if not student.role == 'student':
        #         raise ValidationError(_('Student must have student role.'))


class Course(models.Model):
    name = models.CharField(
        max_length=50,
        verbose_name=_('Course\'s name')
    )
    description = models.TextField()
    head_teacher = models.ForeignKey(
        to='users.User',
        on_delete=models.CASCADE,
        related_name='courses_running',
        verbose_name=_('Head teacher')
    )
    teachers = models.ManyToManyField(
        to='users.User',
        related_name='courses_teaching',
        verbose_name=_('Teachers')
    )
    grade = models.ForeignKey(
        to='courses.Grade',
        on_delete=models.CASCADE,
        related_name='courses',
    )
    code_meu = models.CharField(max_length=30, verbose_name=_('MEU Code'))
    has_exam = models.BooleanField(default=False)
    semester = models.IntegerField()
    language = models.CharField(
        max_length=20, choices=LANGUAGE_CHOICES
    )
    site = models.CharField(max_length=255, verbose_name=_('WWW site'))

    lecture_hours = models.IntegerField()
    labs_hours = models.IntegerField()
    # TODO: additional files

    class Meta:
        ordering = ('name',)
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')

    def __str__(self) -> str:
        return 'Course: {}'.format(self.name)

    def clean(self):
        super().clean()
        # TODO:
        # if not self.head_teacher.role == 'teacher':
        #     raise ValidationError(_('Head teacher must have teacher role'))
        # for teacher in self.teachers.all():
        #     if not teacher.role == 'teacher':
        #         raise ValidationError(_('Teacher must have teacher role'))
