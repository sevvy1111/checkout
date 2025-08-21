# notifications/context_processors.py
from .models import Notification

def notifications_context(request):
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(is_read=False).count()
        recent_notifications = request.user.notifications.all()[:5]
        return {
            'unread_notification_count': unread_count,
            'recent_notifications': recent_notifications
        }
    return {}