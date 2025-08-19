# reports/urls.py
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('create/', views.create_user_report, name='create_user_report'),
]