from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('drop-off/', views.drop_off, name='drop_off'),
    path('receipt/<str:job_id>/', views.receipt, name='receipt'),
    path('track/', views.track_repair, name='track_repair'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/content/', views.dashboard_content, name='dashboard_content'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
    path('job/<str:job_id>/', views.job_detail, name='job_detail'),
    path('job/<str:job_id>/quick-action/', views.job_quick_action, name='job_quick_action'),
    path('job/<str:job_id>/delete/confirm/', views.job_delete_confirm, name='job_delete_confirm'),
    path('job/<str:job_id>/delete/', views.job_delete, name='job_delete'),
    path('total-summary/', views.total_summary, name='total_summary'),
    path('total-summary/filtered/', views.total_summary_filtered, name='total_summary_filtered'),
]
