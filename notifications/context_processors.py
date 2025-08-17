# sevvy1111/checkout/checkout-baa1ef489cd0a3ed08221be9d8b13c13223c8fd8/notifications/context_processors.py
from .models import Notification


def notifications_context(request):
    """
    Provides the count of unread notifications and the latest 5 unread
    notifications for the logged-in user to all templates.
    """
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        # Fetch the 5 most recent unread notifications
        unread_notifications = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).order_by('-timestamp')[:5]

        return {
            'unread_notification_count': unread_count,
            'unread_notifications': unread_notifications,
        }
    return {
        'unread_notification_count': 0,
        'unread_notifications': None,
    }