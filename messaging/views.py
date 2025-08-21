# messaging/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count, Max
from .models import Conversation, Message
from .forms import MessageForm
from django.contrib.auth import get_user_model
from django.contrib import messages
from listings.models import Listing
from django.http import HttpResponseForbidden
from django.urls import reverse

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

        # Get initial message from URL parameter if it exists
        initial_message = ''
        listing_id = self.request.GET.get('listing')
        if listing_id:
            try:
                listing = Listing.objects.get(id=listing_id)
                initial_message = f"Hi, I'm interested in your listing: '{listing.title}'. Can you tell me more about it? ({self.request.build_absolute_uri(listing.get_absolute_url)})"
                messages.info(self.request, "This message has been pre-populated with details about the listing.")
            except Listing.DoesNotExist:
                pass  # Fall back to a blank message if the listing doesn't exist

        context['form'] = MessageForm(initial={'content': initial_message})
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

    # Find an existing conversation
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=recipient
    ).first()

    # If a conversation exists, redirect to it
    if conversation:
        return redirect('messaging:conversation_detail', pk=conversation.pk)

    # If no conversation exists, redirect to the inbox and inform the user
    messages.warning(request, "You need to send your first message to this user to start a conversation.")
    return redirect('messaging:inbox')