# messaging/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Prefetch
from django.contrib.auth.models import User
from django.db import models # New import for models

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
            unread_count=models.Count('messages', filter=models.Q(messages__is_read=False, messages__receiver=self.request.user))
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
        messages = conversation.messages.filter(is_read=False, receiver=self.request.user)
        messages.update(is_read=True)
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
            return redirect('messaging:conversation_detail', pk=conversation.pk)
        else:
            context = self.get_context_data()
            context['form'] = form
            return self.render_to_response(context)


# ... (keep the send_message view as it is) ...
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
            return redirect('messaging:conversation_detail', pk=conversation.pk)
    else:
        form = MessageForm()

    return render(request, 'messaging/send_message.html', {
        'form': form,
        'recipient': recipient,
        'listing': listing
    })