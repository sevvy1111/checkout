# support/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import SupportTicket


@login_required
def chat_view(request):
    # FIX: Delete all previous support tickets for the user to start a fresh conversation.
    SupportTicket.objects.filter(user=request.user).delete()

    # This will now always create a new ticket.
    ticket, created = SupportTicket.objects.get_or_create(user=request.user, status='open')

    return render(request, 'support/chat.html', {'ticket': ticket})