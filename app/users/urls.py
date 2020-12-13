from django.urls import path

from users import views

app_name = 'users'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('schedule/', views.ScheduleView.as_view(), name='schedule'),
    path('notices/', views.NoticeView.as_view(), name='notices'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/<int:pk>/', views.ProfileDetailView.as_view(), name='profile-detail'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile-edit'),
    path('profile/img/delete/', views.delete_profile_image, name='profile-img-delete'),
]
