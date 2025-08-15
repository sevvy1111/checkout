# messages/context_processors.py
from .models import Message

def unread_message_count(request):
    if request.user.is_authenticated:
        unread_count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        return {'unread_message_count': unread_count}
    return {}