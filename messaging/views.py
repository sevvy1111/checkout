# messaging/views.py
# refactor: Centralize and correct timestamp formatting
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Prefetch
from django.contrib.auth.models import User
from django.db import models
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone  # New import

from .models import Conversation, Message
from .forms import MessageForm
from listings.models import Listing


class InboxView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = 'messaging/inbox.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related(
            Prefetch('participants', queryset=User.objects.all().select_related('profile')),
            Prefetch('messages', queryset=Message.objects.order_by('-timestamp'))
        ).annotate(
            unread_count=models.Count('messages',
                                      filter=models.Q(messages__is_read=False, messages__receiver=self.request.user))
        ).order_by('-updated_at')


class ConversationDetailView(LoginRequiredMixin, DetailView):
    model = Conversation
    template_name = 'messaging/conversation_detail.html'
    context_object_name = 'conversation'

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related(
            Prefetch('participants', queryset=User.objects.all().select_related('profile'))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.get_object()
        # Find the other participant in the conversation
        recipient = conversation.participants.exclude(id=self.request.user.id).select_related('profile').first()
        context['recipient'] = recipient
        context['form'] = MessageForm()
        # Mark messages as read
        messages_to_read = conversation.messages.filter(is_read=False, receiver=self.request.user)
        messages_to_read.update(is_read=True)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        conversation = self.get_object()
        recipient = conversation.participants.exclude(id=self.request.user.id).first()
        form = MessageForm(request.POST, request.FILES)

        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.receiver = recipient
            message.save()

            # refactor: Use timezone.localtime for a more robust, locale-aware approach
            timestamp_format = '%b. %d, %Y, %I:%M %p'
            local_time = timezone.localtime(message.timestamp)

            message_data = {
                "type": "chat_message",
                "message": message.text,
                "sender": message.sender.username,
                "timestamp": local_time.strftime(timestamp_format),
                "image_url": message.image.url if message.image else None,
                "temp_id": request.POST.get('temp_id')
            }

            # Broadcast the new message via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{conversation.pk}",
                message_data
            )

            # Fix: Check if it's an AJAX request before returning JsonResponse
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'ok', 'message_data': message_data})
            else:
                return redirect('messaging:conversation_detail', pk=conversation.pk)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
            else:
                return redirect('messaging:conversation_detail', pk=conversation.pk)


@login_required
def send_message(request, username):
    recipient = get_object_or_404(User, username=username)
    listing_id = request.GET.get('listing_id')
    listing = None
    if listing_id:
        listing = get_object_or_404(Listing, id=listing_id)

    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=recipient
    ).first()

    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, recipient)

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.receiver = recipient
            message.save()

            # Broadcast the new message via WebSocket
            channel_layer = get_channel_layer()
            # refactor: Use timezone.localtime for a more robust, locale-aware approach
            timestamp_format = '%b. %d, %Y, %I:%M %p'
            local_time = timezone.localtime(message.timestamp)

            message_data = {
                "type": "chat_message",
                "message": message.text,
                "sender": message.sender.username,
                "timestamp": local_time.strftime(timestamp_format),
                "image_url": message.image.url if message.image else None,
                "temp_id": request.POST.get('temp_id')
            }

            async_to_sync(channel_layer.group_send)(
                f"chat_{conversation.pk}",
                message_data
            )
            # Change this line to redirect to the conversation detail page
            return redirect('messaging:conversation_detail', pk=conversation.pk)
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)
    else:
        form = MessageForm()

    return render(request, 'messaging/send_message.html', {
        'form': form,
        'recipient': recipient,
        'listing': listing
    })