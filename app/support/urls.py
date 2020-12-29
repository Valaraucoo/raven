from django.urls import path

from support import views

app_name = 'support'

urlpatterns = [
    path('contact/', views.TicketCreateView.as_view(), name='support-contact'),
]
