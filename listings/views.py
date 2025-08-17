# listings/views.py
# refactor: Use the custom manager and atomic transactions for better performance and data integrity
import random
import decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.db import transaction, models
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Sum, F, Avg
from django.db.models.functions import Coalesce

from .models import Listing, ListingImage, SavedItem, Review, Cart, CartItem, Checkout
from .forms import ListingForm, ReviewForm, CheckoutForm
from .filters import ListingFilter

# bug: Import the correct messaging model name
from messaging.models import Conversation, Message


class ListingListView(ListView):
    model = Listing
    template_name = 'listings/listing_list.html'
    context_object_name = 'listings'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        # refactor: Use the custom manager method to annotate average rating
        queryset = queryset.select_related('seller').with_avg_rating()
        self.filterset = ListingFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset
        if self.request.user.is_authenticated:
            context['saved_listing_ids'] = SavedItem.objects.filter(
                user=self.request.user
            ).values_list('listing__id', flat=True)
        else:
            context['saved_listing_ids'] = []
        return context


class ListingDetailView(DetailView):
    model = Listing
    template_name = 'listings/listing_detail.html'
    context_object_name = 'listing'

    def get_queryset(self):
        # chore: Prefetch related images and reviews for efficiency
        return super().get_queryset().prefetch_related('images', 'reviews__author__profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.all()
        context['review_form'] = ReviewForm()
        if self.request.user.is_authenticated:
            context['has_reviewed'] = Review.objects.filter(listing=self.object, author=self.request.user).exists()
        else:
            context['has_reviewed'] = False
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = ReviewForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                review = form.save(commit=False)
                review.listing = self.object
                review.author = request.user
                review.save()

                # feature: Notify seller of new review via the messaging app
                seller = self.object.seller
                reviewer = request.user

                if seller != reviewer:
                    # bug: Use the correct model name (Conversation instead of Thread)
                    # Check for an existing conversation between the users
                    conversation = Conversation.objects.filter(participants=seller).filter(
                        participants=reviewer).first()

                    if not conversation:
                        # If no conversation exists, create a new one
                        conversation = Conversation.objects.create()
                        conversation.participants.add(seller, reviewer)

                    message_body = f"A new review with a rating of {review.rating}/5 has been posted on your listing: '{self.object.title}'."
                    # bug: Correctly create a new message with the appropriate fields
                    Message.objects.create(conversation=conversation, sender=reviewer, receiver=seller,
                                           text=message_body)

                    messages.success(request,
                                     "Your review has been posted successfully and the seller has been notified!")
                else:
                    messages.success(request, "Your review has been posted successfully!")

            return redirect(self.object.get_absolute_url())
        else:
            context = self.get_context_data()
            context['review_form'] = form
            return self.render_to_response(context)


class ListingCreateView(LoginRequiredMixin, CreateView):
    model = Listing
    form_class = ListingForm
    template_name = 'listings/listing_create.html'

    def get_success_url(self):
        return reverse('listings:listing_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        with transaction.atomic():
            form.instance.seller = self.request.user
            self.object = form.save()

            images = self.request.FILES.getlist('images')
            for image in images:
                ListingImage.objects.create(listing=self.object, image=image)

        return super().form_valid(form)


class ListingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Listing
    form_class = ListingForm
    template_name = 'listings/listing_update.html'

    def test_func(self):
        return self.get_object().seller == self.request.user

    def get_success_url(self):
        return reverse('listings:listing_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()

            # Handle deletion of old images
            images_to_delete = self.request.POST.getlist('images_to_delete')
            ListingImage.objects.filter(pk__in=images_to_delete).delete()

            # Handle new images
            new_images = self.request.FILES.getlist('images')
            for image in new_images:
                ListingImage.objects.create(listing=self.object, image=image)

        messages.success(self.request, 'Your listing has been updated successfully!')
        return redirect(self.get_success_url())


class ListingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Listing
    template_name = 'listings/listing_confirm_delete.html'
    success_url = reverse_lazy('accounts:dashboard')

    def test_func(self):
        return self.get_object().seller == self.request.user

    # bug: Handle ProtectedError gracefully
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        try:
            self.object.delete()
            messages.success(self.request, f"The listing '{self.object.title}' has been successfully deleted.")
            return redirect(success_url)
        except models.ProtectedError:
            messages.error(request, f"Cannot delete '{self.object.title}' as it has existing orders.")
            return redirect('listings:listing_detail', pk=self.object.pk)


@login_required
def toggle_save_listing(request, pk):
    if request.method == 'POST':
        listing = get_object_or_404(Listing, pk=pk)
        saved_item, created = SavedItem.objects.get_or_create(user=request.user, listing=listing)
        if not created:
            saved_item.delete()
            is_saved = False
        else:
            is_saved = True
        return JsonResponse({'is_saved': is_saved})
    return JsonResponse({'error': 'Invalid request'}, status=400)


def filter_listings(request):
    # refactor: Use the custom manager method
    filter_queryset = Listing.objects.all().select_related('seller').with_avg_rating()
    filter = ListingFilter(request.GET, queryset=filter_queryset)
    saved_listing_ids = []
    if request.user.is_authenticated:
        saved_listing_ids = SavedItem.objects.filter(user=request.user).values_list('listing__id', flat=True)
    context = {
        'filter': filter,
        'saved_listing_ids': saved_listing_ids,
        'user': request.user
    }
    html = render_to_string('listings/partials/listings_grid.html', context)
    return JsonResponse({'html': html})


@login_required
def mark_listing_as_sold(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.user != listing.seller:
        return HttpResponseForbidden()

    if request.method == 'POST':
        # refactor: Use atomic transaction to ensure data integrity
        with transaction.atomic():
            listing.status = 'sold'
            listing.stock = 0  # Set stock to 0 when marked as sold
            listing.save()
            messages.success(request, f"Listing '{listing.title}' has been marked as sold.")
            return redirect('accounts:dashboard')

    return redirect('accounts:dashboard')


@login_required
def add_to_cart(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    cart, created = Cart.objects.get_or_create(user=request.user)

    if listing.stock <= 0:
        messages.error(request, f"Sorry, '{listing.title}' is currently out of stock.")
        return redirect('listings:listing_detail', pk=listing.pk)

    try:
        # refactor: Use atomic transaction to prevent race conditions
        with transaction.atomic():
            cart_item, item_created = CartItem.objects.select_for_update().get_or_create(cart=cart, listing=listing)

            if not item_created:
                # bug: Fix a potential race condition by using F expressions
                if cart_item.quantity < listing.stock:
                    cart_item.quantity = F('quantity') + 1
                    cart_item.save()
                    messages.success(request, f"Added another '{listing.title}' to your cart.")
                else:
                    messages.error(request, f"You have reached the maximum stock available for '{listing.title}'.")
            else:
                messages.success(request, f"Added '{listing.title}' to your cart.")
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")

    return redirect('listings:listing_detail', pk=listing.pk)


@login_required
def view_cart(request):
    cart = get_object_or_404(Cart, user=request.user)
    # chore: Prefetch related items for better performance
    cart_items = cart.items.all().select_related('listing')
    total_price = cart_items.aggregate(
        total_price=Sum(F('quantity') * F('listing__price'))
    )['total_price']
    return render(request, 'listings/cart_detail.html', {'cart_items': cart_items, 'total_price': total_price})


@login_required
def remove_from_cart(request, pk):
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    listing_title = cart_item.listing.title
    cart_item.delete()
    messages.info(request, f"'{listing_title}' was removed from your cart.")
    return redirect('listings:view_cart')


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()

    if not cart_items:
        messages.warning(request, "Your cart is empty. Please add items before checking out.")
        return redirect('listings:view_cart')

    total_price = cart_items.aggregate(
        total_price=Sum(F('quantity') * F('listing__price'))
    )['total_price']

    # feature: Generate a random shipping fee between 100 and 500 for testing
    shipping_fee = decimal.Decimal(str(round(random.uniform(100, 500), 2)))
    grand_total = (total_price or 0) + shipping_fee

    if request.method == 'POST':
        checkout_form = CheckoutForm(request.POST)
        if checkout_form.is_valid():
            # bug: Fix to create one checkout per item, not just one checkout instance for all items
            with transaction.atomic():
                # refactor: Use select_for_update to prevent race conditions
                cart_items = cart.items.all().select_for_update().select_related('listing')

                checkout_ids = []

                # Check stock availability for all items before proceeding
                for item in cart_items:
                    if item.quantity > item.listing.stock:
                        messages.error(request,
                                       f"Checkout failed: Insufficient stock for '{item.listing.title}'. Only {item.listing.stock} available.")
                        return redirect('listings:view_cart')

                # Proceed with checkout if all items are in stock
                for item in cart_items:
                    listing = item.listing

                    # Create a Checkout object for each item
                    checkout_instance = checkout_form.save(commit=False)
                    checkout_instance.user = request.user
                    checkout_instance.listing = listing
                    checkout_instance.quantity = item.quantity

                    # bug: Save shipping fee to the Checkout instance
                    checkout_instance.shipping_fee = shipping_fee

                    checkout_instance.save()
                    checkout_ids.append(checkout_instance.id)

                    # Create a notification for the seller
                    Notification.objects.create(
                        recipient=listing.seller,
                        message=f"You have a new order for '{listing.title}'.",
                        notification_type='new_order',
                        link=reverse('accounts:seller_orders')
                    )

                    # Atomically update stock using F() expression
                    listing.stock = F('stock') - item.quantity
                    if listing.stock == 0:
                        listing.status = 'sold'
                    listing.save()

                    item.delete()

                messages.success(request, "Your order has been placed successfully!")
                return redirect('listings:view_receipt', checkout_ids=','.join(map(str, checkout_ids)))
        else:
            # bug: Add an error message for invalid form data
            messages.error(request,
                           "There was an error with your checkout information. Please check the details below.")
            return render(request, 'listings/checkout.html',
                          {'cart_items': cart_items, 'form': checkout_form, 'total_price': total_price,
                           'shipping_fee': shipping_fee, 'grand_total': grand_total})

    else:
        checkout_form = CheckoutForm()

    return render(request, 'listings/checkout.html',
                  {'cart_items': cart_items, 'form': checkout_form, 'total_price': total_price,
                   'shipping_fee': shipping_fee, 'grand_total': grand_total})


@login_required
def update_cart_item(request, pk):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        try:
            new_quantity = int(request.POST.get('quantity'))

            # bug: Prevent race conditions with atomic transaction and F() expression
            with transaction.atomic():
                item = CartItem.objects.select_for_update().get(pk=pk)
                listing_stock = item.listing.stock

                if new_quantity <= 0:
                    item.delete()
                    messages.info(request, f"'{item.listing.title}' was removed from your cart.")
                elif new_quantity <= listing_stock:
                    item.quantity = new_quantity
                    item.save()
                    messages.success(request, f"Quantity for '{item.listing.title}' updated.")
                else:
                    messages.error(request,
                                   f"Cannot update quantity. Only {listing_stock} stocks are available for '{item.listing.title}'.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity.")

    return redirect('listings:view_cart')


@login_required
def invoice_view(request, pk):
    checkout = get_object_or_404(Checkout, pk=pk, listing__seller=request.user)
    total_price = checkout.listing.price * checkout.quantity
    grand_total = total_price + checkout.shipping_fee
    context = {
        'order': checkout,
        'total_price': total_price,
        'grand_total': grand_total,
    }
    return render(request, 'listings/invoice.html', context)


@login_required
def view_receipt(request, checkout_ids):
    ids = [int(id) for id in checkout_ids.split(',')]
    checkouts = Checkout.objects.filter(id__in=ids, user=request.user).select_related('listing')

    if not checkouts:
        messages.error(request, "Invalid receipt.")
        return redirect('accounts:dashboard')

    subtotal = checkouts.aggregate(
        subtotal=Sum(F('quantity') * F('listing__price'))
    )['subtotal']

    # bug: Correctly calculate grand total by adding subtotal and shipping fee
    shipping_fee = checkouts.first().shipping_fee if checkouts.first() else decimal.Decimal('0.00')
    grand_total = (subtotal or 0) + shipping_fee

    context = {
        'checkouts': checkouts,
        'subtotal': subtotal,
        'grand_total': grand_total,
        'shipping_fee': shipping_fee
    }
    return render(request, 'listings/receipt.html', context)