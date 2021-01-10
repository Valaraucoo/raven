from django.db import models
from django.utils.translation import ugettext_lazy as _


class SupportCategories(models.TextChoices):
    AUTHENTICATION = 'AUTH', _('Authentication Problem')
    FORGET_PASSWORD = 'FPASS', _('Forget Password')
    COMMUNICATION = 'COMM', _('Communication Problem')
    OTHER = 'OTHER', _('Other Problem')


class SupportStatus(models.TextChoices):
    OPEN = 'OPEN', _('Open')
    PROCESSING = 'PROCESSING', _('Processing')
    CLOSED = 'CLOSED', _('Closed')


class SupportTicket(models.Model):
    """
    SupportTicket is a model representing the request reported to support by the user.
    """
    category = models.CharField(max_length=10, choices=SupportCategories.choices)
    email = models.EmailField()
    issuer_fullname = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=SupportStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created_at', 'email',)

    def __str__(self) -> str:
        return f"[{self.category}][{self.status}] {self.email}"
