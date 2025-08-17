# sevvy1111/checkout/checkout-6284e1df24802e516d66595b54136462676a4c2c/messaging/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
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
        return Conversation.objects.filter(participants=self.request.user).order_by('-last_message_time')


class ConversationDetailView(LoginRequiredMixin, DetailView):
    model = Conversation
    template_name = 'messaging/conversation_detail.html'
    context_object_name = 'conversation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conversation = self.get_object()

        # Explicitly find the other participant
        other_user = conversation.participants.exclude(id=self.request.user.id).first()
        context['other_user'] = other_user

        context['form'] = MessageForm()
        # Mark messages as read for the current user
        conversation.messages.filter(receiver=self.request.user, is_read=False).update(is_read=True)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = self.object
            message.sender = request.user
            # Determine the receiver
            participants = self.object.participants.all()
            message.receiver = participants.exclude(id=request.user.id).first()
            message.save()

            return redirect('messaging:conversation_detail', pk=self.object.pk)
        else:
            context = self.get_context_data()
            context['form'] = form
            return self.render_to_response(context)


@login_required
def send_message_view(request, recipient_id):
    recipient = get_object_or_404(User, id=recipient_id)
    if request.user == recipient:
        messages.error(request, "You cannot send a message to yourself.")
        return redirect('listings:listing_list')

    # Find existing conversation or create a new one
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=recipient).first()
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

    return render(request, 'messaging/send_message.html', {'form': form, 'recipient': recipient})