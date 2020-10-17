from django.db import models
from django.contrib.auth import models as auth_models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from users.managers import CustomUserManager


GENDER_CHOICES = (
    ('male', _('Male')),
    ('female', _('Female')),
    ('none', 'none'),
)


class User(auth_models.AbstractUser):
    '''
    Custom User model for eSchool management platform.
    email: PK       used for logging in
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

    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(verbose_name=_('Date joined'), default=timezone.now)
    date_birth = models.DateField(verbose_name=_('Date of birth'), blank=True,
                                  help_text=_('<b>Birthday date in format:</b> YYYY-MM-DD'))

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('first_name', 'last_name',)

    objects = CustomUserManager()

    @property
    def full_username(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.email})"

    def __str__(self):
        return self.full_username
