from django.contrib import admin
from django.db.models import Q
from django.utils import timezone


class CourseStartYearFiler(admin.SimpleListFilter):
    title = 'Filter by start year'
    parameter_name = 'year'

    def lookups(self, request, model_admin):
        year = timezone.now().year
        return (
            ('current', str(year)),
            ('3', f'{year-3} - {year}'),
            ('10', f'{year-10} - {year-3}'),
        )

    def queryset(self, request, queryset):
        year = timezone.now().year
        if self.value() == 'current':
            return queryset.filter(start_year__year=year)
        if self.value() == '3':
            return queryset.filter(start_year__year__gte=year-3)
        if self.value() == '10':
            return queryset.filter(Q(start_year__year__gte=year-10) & Q(start_year__year__lt=year-3))
        return queryset
