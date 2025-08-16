# messaging/urls.py
# chore: Clean up imports
from django.urls import path
from .views import InboxView, ConversationDetailView, send_message

app_name = 'messaging'

urlpatterns = [
    path('', InboxView.as_view(), name='inbox'),
    path('conversation/<int:pk>/', ConversationDetailView.as_view(), name='conversation_detail'),
    # Add the new URL for sending messages
    path('send/<str:username>/', send_message, name='send_message'),
]