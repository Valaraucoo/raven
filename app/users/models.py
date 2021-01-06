import datetime
import os
import uuid

from django.conf import settings
from django.contrib.auth import models as auth_models
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db import models
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from users import managers


def get_file_path(instance, filename: str) -> str:
    today = datetime.date.today().strftime("%Y-%m-%d")
    return os.path.join(settings.UPLOAD_FILES_DIR, today, str(uuid.uuid4()) + filename)


GENDER_CHOICES = (
    ('male', _('Male')),
    ('female', _('Female')),
    ('none', 'none'),
)

ROLE_CHOICES = (
    ('student', _('Student')),
    ('teacher', _('Teacher')),
)


class User(auth_models.AbstractUser):
    '''
    Custom User model for raven platform.

    email: PK                 user's email, used for logging in
    first_name: str           user's first name
    last_name: str            user's last name
    ...

    if role == 'student'
    grade: FK(...)            user's grade/class model
    grades: FK(...)           user's grades

    if role == 'teacher':
    running_courses: FK(...)
    '''
    username = None

    first_name = models.CharField(max_length=30, blank=True, verbose_name=_('First name'))
    last_name = models.CharField(max_length=150, blank=True, verbose_name=_('Last name'))

    email = models.EmailField(unique=True, verbose_name=_('Email address'))
    address = models.CharField(max_length=200, blank=True, verbose_name=_('Address'),
                               help_text=_('<b>Address in format</b>: [STREET NAME] [NUMBER], [CITY]'))
    phone = models.CharField(max_length=9, blank=True, verbose_name=_('Phone number'))
    gender = models.CharField(max_length=10, default='none', choices=GENDER_CHOICES,
                              verbose_name=_("User's gender"))
    role = models.CharField(max_length=9, choices=ROLE_CHOICES)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(verbose_name=_('Date joined'), default=timezone.now)
    date_birth = models.DateField(verbose_name=_('Date of birth'), blank=True, null=True,
                                  help_text=_('<b>Birthday date in format:</b> YYYY-MM-DD'))
    is_online = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True, default="")
    image = models.ImageField(upload_to=get_file_path, default=settings.DEFAULT_USER_IMAGE)
    first_login = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name',)

    objects = managers.CustomUserManager()

    @property
    def full_username(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.email})"

    @property
    def is_student(self) -> bool:
        return self.role == 'student'

    @property
    def is_teacher(self) -> bool:
        return self.role == 'teacher'

    def __str__(self):
        return self.full_username

    def get_absolute_url(self):
        return reverse('users:profile-detail', args=(self.pk,))

    def get_image_url(self):
        return self.image.url


class Teacher(User):
    objects = managers.TeacherUserManager()

    class Meta:
        proxy = True
        verbose_name = _("Teacher")
        verbose_name_plural = _("Teachers")


class Student(User):
    objects = managers.StudentUserManager()

    class Meta:
        proxy = True
        verbose_name = _("Student")
        verbose_name_plural = _("Students")


@receiver(user_logged_in)
def got_online(sender, user, request, **kwargs):
    user.is_online = True
    user.save()


@receiver(user_logged_out)
def got_offline(sender, user, request, **kwargs):
    user.is_online = False
    user.save()
