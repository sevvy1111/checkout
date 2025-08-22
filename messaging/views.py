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
from listings.models import Listing
from django.urls import reverse
from urllib.parse import urlencode
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied

User = get_user_model()


class InboxView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = 'messaging/inbox.html'
    context_object_name = 'conversations'

    def get_queryset(self):
        # Added a message count annotation to filter out empty conversations
        # as a safeguard, ensuring they never appear in the inbox.
        return Conversation.objects.filter(
            participants=self.request.user
        ).annotate(
            message_count=Count('messages')
        ).filter(
            message_count__gt=0
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
    slug_field = 'conversation_key'
    slug_url_kwarg = 'conversation_key'

    def get_object(self, queryset=None):
        """
        Override to handle cases where a conversation doesn't exist yet.
        If the conversation_key is 'new', it means we are creating a new conversation.
        """
        conversation_key = self.kwargs.get(self.slug_url_kwarg)
        if conversation_key == 'new':
            return None  # No object exists yet for a new conversation

        # Use the default manager to avoid issues with custom managers
        queryset = self.model._default_manager.all()

        try:
            return super().get_object(queryset)
        except Http404:
            # Re-raise to ensure proper 404 handling if a specific key is not found
            raise

    def get_context_data(self, **kwargs):
        """
        Prepare context for both existing and new conversations.
        """
        # self.object is set by DetailView's get() method, which calls get_object()
        context = super().get_context_data(**kwargs)
        conversation = self.object

        if conversation:
            if self.request.user not in conversation.participants.all():
                raise PermissionDenied("You do not have access to this conversation.")
            other_user = conversation.get_other_user(self.request.user)
            # Mark messages as read only if the conversation exists
            conversation.messages.filter(receiver=self.request.user, is_read=False).update(is_read=True)
        else:
            # This is a new conversation
            recipient_username = self.request.GET.get('recipient')
            if not recipient_username:
                raise Http404("Recipient not specified for new conversation.")
            other_user = get_object_or_404(User, username=recipient_username)

        context['other_user'] = other_user

        initial_message = ''
        listing_id = self.request.GET.get('listing')

        # Check if conversation exists and has messages
        messages_exist = conversation and conversation.messages.exists()

        if listing_id and not messages_exist:
            try:
                listing = Listing.objects.get(id=listing_id)
                listing_url = self.request.build_absolute_uri(listing.get_absolute_url())
                initial_message = f"Hi, I'm interested in your listing: '{listing.title}'.\n\n{listing_url}"
            except Listing.DoesNotExist:
                pass

        context['form'] = MessageForm(initial={'text': initial_message})
        return context

    def post(self, request, *args, **kwargs):
        """
        Handle message submission. If conversation doesn't exist, create it.
        """
        self.object = self.get_object()  # Sets self.object to None for new conversations
        form = MessageForm(request.POST, request.FILES)

        if form.is_valid():
            conversation = self.object
            recipient = None

            if conversation is None:
                # Conversation doesn't exist, create it now
                recipient_username = request.GET.get('recipient')
                recipient = get_object_or_404(User, username=recipient_username)

                # Use the same method as before to ensure consistency
                conversation = Conversation.objects.get_or_create_conversation(request.user, recipient)
            else:
                recipient = conversation.get_other_user(request.user)

            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.receiver = recipient
            message.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': {
                        'text': message.text,
                        'image_url': message.image.url if message.image else None,
                        'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    },
                    'sender_avatar_url': request.user.profile.display_avatar_url
                })

            return redirect('messaging:conversation_detail', conversation_key=conversation.conversation_key)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

            context = self.get_context_data()
            context['form'] = form
            return self.render_to_response(context)


@login_required
def send_message_view(request, recipient_username):
    """
    Initiates a conversation. Finds an existing conversation or redirects to
    a creation view without creating an empty conversation object.
    """
    recipient = get_object_or_404(User, username=recipient_username)

    if request.user == recipient:
        messages.error(request, "You cannot start a conversation with yourself.")
        return redirect('listings:listing_list')

    # Try to find an existing conversation between the two users
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=recipient
    ).first()

    listing_pk = request.GET.get('listing')
    query_params = {}
    if listing_pk:
        query_params['listing'] = listing_pk

    if conversation:
        # Redirect to the existing conversation
        redirect_url = reverse(
            'messaging:conversation_detail',
            kwargs={'conversation_key': conversation.conversation_key}
        )
    else:
        # No conversation exists, redirect to the detail view in 'new' mode
        redirect_url = reverse(
            'messaging:conversation_detail',
            kwargs={'conversation_key': 'new'}
        )
        # Pass the recipient in the query params for the view to use
        query_params['recipient'] = recipient_username

    if query_params:
        redirect_url = f"{redirect_url}?{urlencode(query_params)}"

    return redirect(redirect_url)