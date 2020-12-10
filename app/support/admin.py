from django.contrib import admin
from .models import SupportTicket


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_filter = ('status', 'category',)
    list_display = ('email', 'issuer_fullname', 'status', 'category', 'created_at',)
    search_fields = ('email', 'issuer_fullname',)
