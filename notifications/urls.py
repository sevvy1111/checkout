# notifications/urls.py
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.all_notifications, name='all'),
    path('read/<int:notification_id>/', views.read_and_redirect, name='read_and_redirect'),
]