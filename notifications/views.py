# sevvy1111/checkout/checkout-6284e1df24802e516d66595b54136462676a4c2c/notifications/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.http import JsonResponse
from .models import Notification


class NotificationListView(ListView):
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        # First, mark all unread notifications as read when visiting this page
        Notification.objects.filter(recipient=self.request.user, is_read=False).update(is_read=True)
        # Then, return all notifications for the user
        return Notification.objects.filter(recipient=self.request.user).order_by('-timestamp')


@login_required
def mark_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications:all')


@login_required
def redirect_and_mark_as_read(request, notification_id):
    """
    Marks a specific notification as read and then redirects the user
    to the notification's link.
    """
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()

    if notification.link:
        return redirect(notification.link)

    # Fallback in case there is no link
    return redirect('notifications:all')