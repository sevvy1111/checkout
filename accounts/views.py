# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView
from django.contrib.auth import get_user_model
from django.urls import reverse
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from listings.forms import OrderStatusForm
from listings.models import Listing, SavedItem, Order
from notifications.models import Notification

User = get_user_model()


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('accounts:profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def dashboard(request):
    user_listings = Listing.objects.filter(seller=request.user).order_by('-created')
    context = {'listings': user_listings}
    return render(request, 'accounts/dashboard.html', context)


@login_required
def saved_listings(request):
    saved = SavedItem.objects.filter(user=request.user).select_related('listing').order_by('-saved_at')
    context = {'saved_items': saved}
    return render(request, 'accounts/saved_listings.html', context)


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__listing').order_by('-created_at')
    return render(request, 'accounts/order_history.html', {'orders': orders})


@login_required
def seller_orders(request):
    orders = Order.objects.filter(items__listing__seller=request.user).distinct().order_by('-created_at')
    orders = orders.prefetch_related('items__listing__images')

    forms = {order.id: OrderStatusForm(instance=order) for order in orders}
    context = {
        'orders': orders,
        'forms': forms,
    }
    return render(request, 'accounts/seller_orders.html', context)


@login_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    # Use the centralized model method for the permission check
    if not order.is_seller(request.user):
        messages.error(request, "You do not have permission to modify this order.")
        return redirect('accounts:seller_orders')

    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f"Order #{order.id} status has been updated.")

            # Notify the buyer about the status update
            Notification.objects.create(
                recipient=order.user,
                message=f"The status of your order #{order.id} has been updated to '{order.get_status_display()}'.",
                notification_type='order_status_update',
                link=reverse('accounts:order_history')
            )

    return redirect('accounts:seller_orders')


class PublicProfileDetailView(DetailView):
    model = User
    template_name = 'accounts/profile_detail.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['user_listings'] = Listing.objects.filter(seller=user, status='available').order_by('-created')

        # Add a list of saved listing IDs for the current authenticated user
        if self.request.user.is_authenticated:
            context['saved_listing_ids'] = SavedItem.objects.filter(
                user=self.request.user
            ).values_list('listing__id', flat=True)
        else:
            context['saved_listing_ids'] = []

        # Refactored: Use the efficient method from the profile model
        context['seller_average_rating'] = user.profile.get_seller_average_rating()

        return context