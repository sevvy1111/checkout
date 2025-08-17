# messaging/context_processors.py
from .models import Message, Conversation

def unread_message_count(request):
    if request.user.is_authenticated:
        unread_count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        return {'unread_message_count': unread_count}
    return {}

def all_conversations(request):
    if request.user.is_authenticated:
        conversations = Conversation.objects.filter(participants=request.user)
        return {'all_conversations': conversations}
    return {}