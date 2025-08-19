# messaging/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from .models import Conversation, Message
from .forms import MessageForm
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model()


class InboxView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = 'messaging/inbox.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        # Annotate each conversation with the count of unread messages for the current user
        return Conversation.objects.filter(
            participants=self.request.user
        ).annotate(
            unread_count=Count('messages', filter=Q(messages__receiver=self.request.user, messages__is_read=False))
        ).prefetch_related(
            'participants__profile', 'messages'
        ).order_by('-last_message_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversations_with_user = []
        for conversation in context['conversations']:
            other_user = conversation.get_other_user(self.request.user)
            if other_user:
                conversation.other_user = other_user
                conversations_with_user.append(conversation)
        context['conversations'] = conversations_with_user
        return context


class ConversationDetailView(LoginRequiredMixin, DetailView):
    model = Conversation
    template_name = 'messaging/conversation_detail.html'
    context_object_name = 'conversation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.get_object()

        other_user = conversation.get_other_user(self.request.user)
        context['other_user'] = other_user

        context['form'] = MessageForm()
        # Mark messages as read upon opening the conversation
        conversation.messages.filter(receiver=self.request.user, is_read=False).update(is_read=True)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = self.object
            message.sender = request.user
            message.receiver = self.object.get_other_user(request.user)
            message.save()
            return redirect('messaging:conversation_detail', pk=self.object.pk)
        else:
            context = self.get_context_data()
            context['form'] = form
            return self.render_to_response(context)


@login_required
def send_message_view(request, recipient_username):
    recipient = get_object_or_404(User, username=recipient_username)
    if request.user == recipient:
        messages.error(request, "You cannot send a message to yourself.")
        return redirect('listings:listing_list')

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
            messages.success(request, "Your message has been sent.")
            return redirect('messaging:conversation_detail', pk=conversation.pk)
    else:
        return redirect('messaging:conversation_detail', pk=conversation.pk)

    messages.error(request, "There was an error sending your message.")
    return redirect(request.META.get('HTTP_REFERER', 'listings:listing_list'))