# support/urls.py
from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('chat/', views.chat_view, name='chat'),
]