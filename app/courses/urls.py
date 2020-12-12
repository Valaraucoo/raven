from django.urls import include, path
from rest_framework import routers

from courses import views
from courses.api.views import (CourseListView, CourseViewSet,
                               additional_course_student)

app_name = 'courses'

router = routers.SimpleRouter()
router.register('api/courses', CourseViewSet)

urlpatterns = [
    path('courses/', views.CourseView.as_view(), name='courses'),
    path('courses/<slug:the_slug>/', views.CoursesDetailView.as_view(), name='courses-detail'),
    path('courses/<slug:the_slug>/edit/', views.CourseEditView.as_view(), name='courses-edit'),
    path('courses/<slug:the_slug>/delete/<int:num>/', views.delete_lecture_view, name='lectures-delete'),

    path('courses/lecture/<int:pk>/detail/', views.LectureDetailView.as_view(), name='lectures-detail'),
    path('courses/lecture/<int:pk>/edit/', views.LectureEditView.as_view(), name='lectures-edit'),
    path('courses/lecture/<int:pk>/file/add/', views.lecture_add_file, name='lectures-file-add'),
    path('courses/lecture/<int:pk>/file/delete/<int:num>', views.delete_lecture_file, name='lectures-file-delete'),
    path('courses/<slug:the_slug>/lecture/create/', views.LectureCreateView.as_view(), name='lectures-create'),

    path('courses/laboratory/<int:pk>/', views.LaboratoryDetailView.as_view(), name='laboratory-detail'),
    path('courses/laboratory/<int:pk>/edit/', views.LaboratoryEditView.as_view(), name='laboratory-edit'),
    path('courses/<slug:the_slug>/laboratory/create/', views.LaboratoryCreateView.as_view(), name='laboratory-create'),
    path('courses/laboratory/<int:pk>/file/add/', views.laboratory_add_file, name='laboratory-file-add'),
    path('courses/laboratory/<int:pk>/file/delete/<int:num>/', views.delete_laboratory_file,
         name='laboratory-file-delete'),

    path('courses/<slug:the_slug>/groups/', views.CourseGroupJoinListView.as_view(), name='group'),
    path('courses/<slug:the_slug>/groups/create/', views.course_group_create_view, name='group-create'),
    path('courses/<slug:the_slug>/groups/join/<int:num>', views.course_group_join_view, name='group-join-group'),
    path('courses/groups/<int:pk>/', views.CourseGroupEditView.as_view(), name='group-edit'),
    path('courses/<slug:the_slug>/groups/<int:num>/delete/', views.course_group_delete_view, name='group-delete'),

    path('courses/<slug:the_slug>/notices/', views.CourseNoticeView.as_view(), name='notices'),

    path('', include(router.urls)),
    path('api/list/courses/', CourseListView.as_view()),
    path('api/courses/<slug:the_slug>/additional-student/', additional_course_student),
]
