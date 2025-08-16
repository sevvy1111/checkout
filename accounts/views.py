# accounts/views.py
# refactor: Remove duplicate view and handle forms more robustly
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count
import random

from listings.models import Listing, Review, SavedItem, Checkout
from listings.forms import OrderStatusForm
from .forms import RegistrationForm, ProfileForm, PhoneVerificationForm


@login_required
def profile_view(request):
    profile = request.user.profile
    # fix: Handle both text and file data in one form submission
    if request.method == 'POST':
        p_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if p_form.is_valid():
            p_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        p_form = ProfileForm(instance=profile)

    user_listings = Listing.objects.filter(seller=request.user).order_by('-created')

    context = {
        'p_form': p_form,
        'user_listings': user_listings
    }
    return render(request, 'accounts/profile.html', context)


# ... (The rest of your views remain unchanged) ...
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('listings:listing_list')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def public_profile_view(request, username):
    user = get_object_or_404(User, username=username)
    profile = user.profile
    user_listings = Listing.objects.filter(seller=user).order_by('-created')
    context = {
        'user': user,
        'profile': profile,
        'user_listings': user_listings,
    }
    return render(request, 'accounts/profile_detail.html', context)


@login_required
def dashboard_view(request):
    user = request.user
    listings = Listing.objects.filter(seller=user).annotate(saved_count=Count('saved_by'))
    reviews = Review.objects.filter(listing__seller=user)

    context = {
        'listings': listings,
        'reviews': reviews,
        'total_listings': listings.count(),
        'active_listings': listings.filter(status='available').count(),
        'sold_listings': listings.filter(status='sold').count(),
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def saved_listings_view(request):
    saved_items = SavedItem.objects.filter(user=request.user).select_related('listing__seller')
    return render(request, 'accounts/saved_listings.html', {'saved_items': saved_items})


@login_required
def send_verification_code_view(request):
    profile = request.user.profile
    if not profile.phone:
        messages.error(request, "Please add a phone number to your profile first.")
        return redirect('accounts:profile')
    code = str(random.randint(100000, 999999))
    profile.phone_verification_code = code
    profile.save()
    messages.info(request, f"For testing purposes, your verification code is: {code}")
    return redirect('accounts:verify_phone')


@login_required
def verify_phone_view(request):
    profile = request.user.profile
    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data['code']
            if entered_code == profile.phone_verification_code:
                profile.is_phone_verified = True
                profile.phone_verification_code = None
                profile.save()
                messages.success(request, "Your phone number has been verified!")
                return redirect('accounts:profile')
            else:
                messages.error(request, "Invalid verification code. Please try again.")
    else:
        form = PhoneVerificationForm()
    return render(request, 'accounts/verify_phone.html', {'form': form})


# New view for Order History
@login_required
def order_history_view(request):
    checkouts = Checkout.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/order_history.html', {'checkouts': checkouts})


# New view for Seller Orders
@login_required
def seller_orders_view(request):
    seller_checkouts = Checkout.objects.filter(listing__seller=request.user).order_by('-created_at')
    forms = {checkout.id: OrderStatusForm(instance=checkout) for checkout in seller_checkouts}
    return render(request, 'accounts/seller_orders.html', {'seller_checkouts': seller_checkouts, 'forms': forms})


# fix: Removed the duplicate `update_order_status_view` function.
@login_required
def update_order_status_view(request, pk):
    if request.method == 'POST':
        checkout_item = get_object_or_404(Checkout, pk=pk, listing__seller=request.user)
        form = OrderStatusForm(request.POST, instance=checkout_item)
        if form.is_valid():
            form.save()
            messages.success(request,
                             f"Order for '{checkout_item.listing.title}' has been updated to '{checkout_item.status}'.")
        else:
            messages.error(request, "Invalid form submission.")
    return redirect('accounts:seller_orders')


@login_required
def receipt_view(request, pk):
    receipt = get_object_or_404(Checkout, pk=pk, user=request.user)

    total_price = receipt.listing.price * receipt.quantity

    context = {
        'receipt': receipt,
        'total_price': total_price,
    }
    return render(request, 'accounts/receipt.html', context)