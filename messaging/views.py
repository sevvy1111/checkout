from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
from .models import Conversation, Message
from .forms import MessageForm
from django.contrib.auth import get_user_model
from django.contrib import messages
from listings.models import Listing
from django.urls import reverse
from urllib.parse import urlencode
from django.http import JsonResponse, HttpResponseBadRequest

User = get_user_model()


class InboxView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = 'messaging/inbox.html'
    context_object_name = 'conversations'

    def get_queryset(self):
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

        if self.request.user not in conversation.participants.all():
            raise PermissionDenied("You do not have access to this conversation.")

        other_user = conversation.get_other_user(self.request.user)
        context['other_user'] = other_user

        initial_message = ''
        listing_id = self.request.GET.get('listing')
        if listing_id and not conversation.messages.exists():
            try:
                listing = Listing.objects.get(id=listing_id)
                listing_url = self.request.build_absolute_uri(listing.get_absolute_url())
                initial_message = f"Hi, I'm interested in your listing: '{listing.title}'.\n\n{listing_url}"
            except Listing.DoesNotExist:
                pass

        context['form'] = MessageForm(initial={'content': initial_message})

        # Mark messages as read
        conversation.messages.filter(receiver=self.request.user, is_read=False).update(is_read=True)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = MessageForm(request.POST, request.FILES)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if form.is_valid():
                message = form.save(commit=False)
                message.conversation = self.object
                message.sender = request.user
                message.receiver = self.object.get_other_user(request.user)
                message.save()

                # Update conversation's last message time
                self.object.last_message_time = message.timestamp
                self.object.save()

                return JsonResponse({
                    'status': 'success',
                    'message': {
                        'text': message.text,
                        'image_url': message.image.url if message.image else None,
                        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    },
                    'sender_avatar_url': request.user.profile.display_avatar_url
                })
            else:
                return JsonResponse({'status': 'error', 'message': form.errors}, status=400)

        # Fallback for non-AJAX requests
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
        messages.error(request, "You cannot start a conversation with yourself.")
        return redirect('listings:listing_list')

    conversation = Conversation.objects.get_or_create_conversation(
        request.user,
        recipient
    )

    redirect_url = reverse(
        'messaging:conversation_detail',
        kwargs={'pk': conversation.pk}
    )

    listing_pk = request.GET.get('listing')
    if listing_pk:
        query_params = urlencode({'listing': listing_pk})
        redirect_url = f"{redirect_url}?{query_params}"

    return redirect(redirect_url)