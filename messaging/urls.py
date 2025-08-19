# messaging/urls.py
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.InboxView.as_view(), name='inbox'),
    path('conversation/<int:pk>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    # Corrected URL to handle sending a message by username
    path('send/<str:recipient_username>/', views.send_message_view, name='send_message'),
]