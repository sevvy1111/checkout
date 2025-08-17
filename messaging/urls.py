# sevvy1111/checkout/checkout-6284e1df24802e516d66595b54136462676a4c2c/messaging/urls.py
from django.urls import path
from .views import InboxView, ConversationDetailView, send_message_view

app_name = 'messaging'

urlpatterns = [
    path('inbox/', InboxView.as_view(), name='inbox'),
    path('conversation/<int:pk>/', ConversationDetailView.as_view(), name='conversation_detail'),
    # Also, correct the view name used in the path
    path('send/<int:recipient_id>/', send_message_view, name='send_message'),
]