# notifications/urls.py
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='all'),
    path('mark-as-read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
    path('read/<int:notification_id>/', views.redirect_and_mark_as_read, name='read_and_redirect'),
]