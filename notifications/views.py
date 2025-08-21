# notifications/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def all_notifications(request):
    notifications = request.user.notifications.all()
    return render(request, 'notifications/all.html', {'notifications': notifications})

@login_required
def read_and_redirect(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)

    if not notification.is_read:
        notification.is_read = True
        notification.save()

    if notification.link:
        return redirect(notification.link)

    return redirect('notifications:all')