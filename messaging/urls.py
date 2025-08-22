# messaging/urls.py
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.InboxView.as_view(), name='inbox'),
    # Use the unique conversation_key (string) instead of the primary key
    path('conversation/<str:conversation_key>/', views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('send/<str:recipient_username>/', views.send_message_view, name='send_message'),
]