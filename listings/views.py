# listings/views.py
import random
import decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.db import transaction, models
from django.http import JsonResponse, HttpResponseForbidden, Http404
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Sum, F, Avg

from .filters import ListingFilter
from .models import Listing, ListingImage, SavedItem, Review, Cart, CartItem, Order, OrderItem, Category
from .forms import ListingForm, ReviewForm, OrderForm

from messaging.models import Conversation, Message
from notifications.models import Notification


class ListingListView(ListView):
    model = Listing
    template_name = 'listings/listing_list.html'
    context_object_name = 'listings'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset().select_related('seller').prefetch_related('images').with_avg_rating()
        self.filterset = ListingFilter(self.request.GET, queryset=queryset)
        return self.filterset.qs.order_by('-created')

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
        return super().get_queryset().prefetch_related('images', 'reviews__author__profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.all()
        context['review_form'] = ReviewForm()

        if self.request.user.is_authenticated:
            context['has_reviewed'] = self.object.reviews.filter(author=self.request.user).exists()
            context['is_saved'] = SavedItem.objects.filter(listing=self.object, user=self.request.user).exists()
        else:
            context['has_reviewed'] = False
            context['is_saved'] = False

        seller = self.object.seller
        seller_average_rating = Review.objects.filter(listing__seller=seller).aggregate(Avg('rating'))['rating__avg']
        context['seller_average_rating'] = seller_average_rating

        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        self.object = self.get_object()
        form = ReviewForm(request.POST)

        if form.is_valid():
            with transaction.atomic():
                review = form.save(commit=False)
                review.listing = self.object
                review.author = request.user
                review.save()

                seller = self.object.seller
                if seller != request.user:
                    Notification.objects.create(
                        recipient=seller,
                        message=f"You received a new {review.rating}-star review on '{self.object.title}'.",
                        notification_type='new_review',
                        link=self.object.get_absolute_url()
                    )
                    messages.success(request, "Your review has been posted and the seller has been notified!")
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

        messages.success(self.request, 'Your listing has been created successfully!')
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
            images_to_delete = self.request.POST.getlist('images_to_delete')
            if images_to_delete:
                ListingImage.objects.filter(pk__in=images_to_delete).delete()

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

    def form_valid(self, form):
        try:
            self.object = self.get_object()
            self.object.delete()
            messages.success(self.request, f"The listing '{self.object.title}' has been successfully deleted.")
            return redirect(self.get_success_url())
        except models.ProtectedError:
            messages.error(self.request, f"Cannot delete '{self.object.title}' as it is part of an existing order.")
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
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def filter_listings(request):
    filter_queryset = Listing.objects.all().select_related('seller').with_avg_rating()
    listing_filter = ListingFilter(request.GET, queryset=filter_queryset)

    saved_listing_ids = []
    if request.user.is_authenticated:
        saved_listing_ids = SavedItem.objects.filter(user=request.user).values_list('listing__id', flat=True)

    context = {
        'filter': listing_filter,
        'listings': listing_filter.qs,
        'saved_listing_ids': saved_listing_ids,
        'user': request.user
    }
    html = render_to_string('listings/partials/listings_grid.html', context)
    return JsonResponse({'html': html})


@login_required
def mark_listing_as_sold(request, pk):
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == 'POST':
        with transaction.atomic():
            listing.status = 'sold'
            listing.stock = 0
            listing.save()
        messages.success(request, f"Listing '{listing.title}' has been marked as sold.")
    return redirect('accounts:dashboard')


@login_required
def add_to_cart(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if listing.stock <= 0:
        messages.error(request, f"Sorry, '{listing.title}' is currently out of stock.")
        return redirect('listings:listing_detail', pk=listing.pk)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    with transaction.atomic():
        cart_item, created = CartItem.objects.select_for_update().get_or_create(cart=cart, listing=listing)
        if not created:
            if cart_item.quantity < listing.stock:
                cart_item.quantity = F('quantity') + 1
                cart_item.save()
                messages.success(request, f"Added another '{listing.title}' to your cart.")
            else:
                messages.warning(request,
                                 f"You already have the maximum available stock for '{listing.title}' in your cart.")
        else:
            messages.success(request, f"Added '{listing.title}' to your cart.")
    return redirect('listings:listing_detail', pk=listing.pk)


@login_required
def view_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('listing').prefetch_related('listing__images').all()
    subtotal = sum(item.total_price for item in cart_items)
    return render(request, 'listings/cart_detail.html', {'cart_items': cart_items, 'subtotal': subtotal})


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
    cart_items = cart.items.select_related('listing').all()
    if not cart_items:
        messages.warning(request, "Your cart is empty. Add items before checking out.")
        return redirect('listings:view_cart')
    subtotal = sum(item.total_price for item in cart_items)
    shipping_fee = decimal.Decimal(str(round(random.uniform(50, 250), 2)))
    grand_total = (subtotal or 0) + shipping_fee
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                for item in cart_items:
                    listing = item.listing
                    listing.refresh_from_db()
                    if item.quantity > listing.stock:
                        messages.error(request,
                                       f"Checkout failed: Insufficient stock for '{listing.title}'. Only {listing.stock} available.")
                        return redirect('listings:view_cart')
                order = form.save(commit=False)
                order.user = request.user
                order.shipping_fee = shipping_fee
                order.total_price = grand_total
                order.save()
                for item in cart_items:
                    listing = item.listing
                    OrderItem.objects.create(
                        order=order,
                        listing=listing,
                        quantity=item.quantity,
                        price=listing.price
                    )
                    listing.stock = F('stock') - item.quantity
                    if listing.stock == 0:
                        listing.status = 'sold'
                    listing.save()
                    Notification.objects.create(
                        recipient=listing.seller,
                        message=f"You have a new order for '{listing.title}'.",
                        notification_type='new_order',
                        link=reverse('accounts:seller_orders')
                    )
                cart.items.all().delete()
                messages.success(request, "Your order has been placed successfully!")
                return redirect('listings:view_receipt', pk=order.pk)
        else:
            messages.error(request, "There was an error with your information. Please check the details below.")
    else:
        form = OrderForm()
    context = {
        'cart_items': cart_items,
        'form': form,
        'subtotal': subtotal,
        'shipping_fee': shipping_fee,
        'grand_total': grand_total
    }
    return render(request, 'listings/checkout.html', context)


@login_required
def update_cart_item(request, pk):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        try:
            new_quantity = int(request.POST.get('quantity'))
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
                                   f"Cannot update quantity. Only {listing_stock} units are available for '{item.listing.title}'.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity provided.")
    return redirect('listings:view_cart')


@login_required
def seller_order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    seller_items = order.items.filter(listing__seller=request.user).select_related('listing')
    if not seller_items.exists():
        raise Http404("No items belonging to you were found in this order.")
    context = {
        'order': order,
        'seller_items': seller_items
    }
    return render(request, 'listings/seller_order_detail.html', context)


@login_required
def view_receipt(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    order_items = order.items.select_related('listing').prefetch_related('listing__images').all()
    context = {
        'order': order,
        'order_items': order_items,
        'subtotal': order.total_price - order.shipping_fee,
    }
    return render(request, 'listings/receipt.html', context)


def search_suggestions(request):
    query = request.GET.get('q', '')
    data = []
    # FIX: Changed condition to trigger on the first character
    if len(query) > 0:
        listings = Listing.objects.filter(title__icontains=query, status='available').prefetch_related('images')[:5]
        for listing in listings:
            first_image = listing.images.first()
            data.append({
                'title': listing.title,
                'url': listing.get_absolute_url(),
                'image_url': first_image.image.url if first_image else 'https://via.placeholder.com/40x40?text=No+Img'
            })
    return JsonResponse({'suggestions': data})