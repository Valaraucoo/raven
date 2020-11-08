from django.urls import path

from courses import views

app_name = 'courses'

urlpatterns = [
    path('courses/', views.CourseView.as_view(), name='courses'),
    path('courses/<slug:the_slug>/', views.CoursesDetailView.as_view(), name='courses-detail'),
]
