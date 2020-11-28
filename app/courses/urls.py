from django.urls import path, include
from rest_framework import routers

from courses import views
from courses.api.views import CourseViewSet, additional_course_student, CourseListView

app_name = 'courses'

router = routers.SimpleRouter()
router.register('api/courses', CourseViewSet)

urlpatterns = [
    path('courses/', views.CourseView.as_view(), name='courses'),
    path('courses/<slug:the_slug>/', views.CoursesDetailView.as_view(), name='courses-detail'),
    path('courses/<slug:the_slug>/edit/', views.CourseEditView.as_view(), name='courses-edit'),
    path('', include(router.urls)),
    path('api/list/courses/', CourseListView.as_view()),
    path('api/courses/<slug:the_slug>/additional-student/', additional_course_student),
]
