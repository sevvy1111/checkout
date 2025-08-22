# listings/views.py
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
from django.db.models import F, Avg

from .filters import ListingFilter
from .models import Listing, ListingImage, SavedItem, Review, Cart, CartItem, Order, OrderItem, Category
from .forms import ListingForm, ReviewForm, OrderForm

from messaging.models import Conversation, Message
from notifications.models import Notification


class ListingListView(ListView):
    """
    View for listing all available listings with filtering and pagination.
    """
    model = Listing
    template_name = 'listings/listing_list.html'
    context_object_name = 'listings'
    paginate_by = 12

    def get_queryset(self):
        """
        Returns a filtered and optimized queryset for listings.
        """
        base_queryset = super().get_queryset().select_related('seller').prefetch_related(
            'images').with_avg_rating().order_by('-featured', '-created')
        self.filterset = ListingFilter(self.request.GET, queryset=base_queryset)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        """
        Adds filter and saved listing IDs to the context.
        """
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset

        page_title = "Find Deals"
        search_query = self.request.GET.get('q')
        category_param = self.request.GET.get('category')
        city_name = self.request.GET.get('city')
        category = None

        if category_param:
            try:
                category = Category.objects.get(pk=int(category_param))
            except (ValueError, TypeError, Category.DoesNotExist):
                try:
                    category = Category.objects.get(name__iexact=category_param)
                except Category.DoesNotExist:
                    category = None

        if search_query:
            page_title = f"Search Results for '{search_query}'"
        elif category:
            page_title = f"Deals in {category.name}"
            if city_name:
                page_title = f"{category.name} in {city_name.title()}"
        elif city_name:
            page_title = f"Deals in {city_name.title()}"

        context['page_title'] = page_title

        if self.request.user.is_authenticated:
            context['saved_listing_ids'] = SavedItem.objects.filter(
                user=self.request.user
            ).values_list('listing__id', flat=True)
        else:
            context['saved_listing_ids'] = []
        return context


class ListingDetailView(DetailView):
    """
    View for a single listing, including its details and reviews.
    """
    model = Listing
    template_name = 'listings/listing_detail.html'
    context_object_name = 'listing'

    def get_queryset(self):
        """
        Optimizes the queryset for listing details.
        """
        return super().get_queryset().prefetch_related(
            'images', 'reviews__author__profile'
        ).annotate(
            average_rating=Avg('reviews__rating')
        )

    def get_context_data(self, **kwargs):
        """
        Adds review form, review status, and seller rating to the context.
        """
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.all()
        context['review_form'] = ReviewForm()

        can_review_items = []

        if self.request.user.is_authenticated:
            context['has_reviewed'] = self.object.reviews.filter(author=self.request.user).exists()
            context['is_saved'] = SavedItem.objects.filter(listing=self.object, user=self.request.user).exists()

            # Find delivered order items for this listing that have not been reviewed
            can_review_items = OrderItem.objects.filter(
                order__user=self.request.user,
                order__status='delivered',
                listing=self.object,
                review__isnull=True  # Exclude items that have already been reviewed
            ).values('id', 'quantity')

        else:
            context['has_reviewed'] = False
            context['is_saved'] = False

        context['can_review_items'] = can_review_items
        context['can_review'] = bool(can_review_items)

        # Use the centralized method from the profile model
        context['seller_average_rating'] = self.object.seller.profile.get_seller_average_rating()
        return context

    def post(self, request, *args, **kwargs):
        """
        Handles the creation of a new review for the listing.
        """
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        self.object = self.get_object()
        form = ReviewForm(request.POST)

        order_item_id = request.POST.get('order_item_id')
        if not order_item_id:
            messages.error(request, "Missing order item information.")
            return redirect(self.object.get_absolute_url())

        order_item = get_object_or_404(OrderItem, pk=order_item_id)

        # Security check: Ensure the user is the buyer and the order is delivered and not yet reviewed
        if not (order_item.order.user == request.user and
                order_item.order.status == 'delivered' and
                not hasattr(order_item, 'review')):
            messages.error(request,
                           "You are not authorized to leave a review for this item or it has already been reviewed.")
            return redirect(self.object.get_absolute_url())

        # Security check: Ensure the user is not the seller
        if request.user == self.object.seller:
            messages.error(request, "You cannot review your own listing.")
            return redirect(self.object.get_absolute_url())

        if form.is_valid():
            with transaction.atomic():
                review = form.save(commit=False)
                review.listing = self.object
                review.author = request.user
                review.order_item = order_item
                review.save()

                seller = self.object.seller
                # Fix: Don't notify the seller if they are the one leaving the review.
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
    """
    View for creating a new listing.
    """
    model = Listing
    form_class = ListingForm
    template_name = 'listings/listing_create.html'

    def get_context_data(self, **kwargs):
        """
        Adds categories to the context.
        """
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context

    def get_success_url(self):
        return reverse('listings:listing_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        """
        Saves the new listing and associated images.
        """
        with transaction.atomic():
            form.instance.seller = self.request.user
            self.object = form.save()

            images = self.request.FILES.getlist('images')
            if images:
                ListingImage.objects.bulk_create([
                    ListingImage(listing=self.object, image=image) for image in images
                ])

        messages.success(self.request, 'Your listing has been created successfully!')
        return super().form_valid(form)


class ListingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating an existing listing.
    """
    model = Listing
    form_class = ListingForm
    template_name = 'listings/listing_update.html'

    def test_func(self):
        return self.get_object().seller == self.request.user

    def get_success_url(self):
        return reverse('listings:listing_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        """
        Saves updated listing details and handles image updates.
        """
        with transaction.atomic():
            self.object = form.save()
            images_to_delete = self.request.POST.getlist('images_to_delete')
            if images_to_delete:
                ListingImage.objects.filter(pk__in=images_to_delete).delete()

            new_images = self.request.FILES.getlist('images')
            if new_images:
                ListingImage.objects.bulk_create([
                    ListingImage(listing=self.object, image=image) for image in new_images
                ])

        messages.success(self.request, 'Your listing has been updated successfully!')
        return redirect(self.get_success_url())


class ListingDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting a listing, with protection against deleting listings in orders.
    """
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
    """
    Toggles saving/unsaving a listing to a user's wishlist via AJAX.
    """
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
    """
    Filters listings and returns the HTML for the listings grid via AJAX.
    """
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
    """
    Marks a listing as sold and sets stock to zero.
    """
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
    """
    Adds a listing to the user's shopping cart, preventing race conditions.
    """
    listing = get_object_or_404(Listing, pk=pk)
    cart, _ = Cart.objects.get_or_create(user=request.user)

    with transaction.atomic():
        # Lock the listing row to prevent race conditions
        listing_for_update = Listing.objects.select_for_update().get(pk=listing.pk)

        if listing_for_update.stock <= 0:
            messages.error(request, f"Sorry, '{listing_for_update.title}' is currently out of stock.")
            return redirect('listings:listing_detail', pk=listing_for_update.pk)

        cart_item, created = CartItem.objects.get_or_create(cart=cart, listing=listing_for_update)

        if created:
            messages.success(request, f"Added '{listing_for_update.title}' to your cart.")
        else:
            if cart_item.quantity < listing_for_update.stock:
                cart_item.quantity = F('quantity') + 1
                cart_item.save()
                messages.success(request, f"Added another '{listing_for_update.title}' to your cart.")
            else:
                messages.warning(request,
                                 f"You already have the maximum available stock for '{listing_for_update.title}' in your cart.")

    return redirect('listings:listing_detail', pk=listing.pk)


@login_required
def view_cart(request):
    """
    Displays the user's shopping cart.
    """
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.select_related('listing').prefetch_related('listing__images').all()
    subtotal = sum(item.total_price for item in cart_items)
    shipping_fee = decimal.Decimal('75.00')
    grand_total = subtotal + shipping_fee
    return render(request, 'listings/cart_detail.html',
                  {'cart_items': cart_items, 'subtotal': subtotal, 'grand_total': grand_total, 'cart': cart})


@login_required
def remove_from_cart(request, pk):
    """
    Removes an item from the user's cart.
    """
    cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
    listing_title = cart_item.listing.title
    cart_item.delete()
    messages.info(request, f"'{listing_title}' was removed from your cart.")
    return redirect('listings:view_cart')


@login_required
def remove_from_saved(request, pk):
    """
    Removes a listing from the user's wishlist.
    """
    saved_item = get_object_or_404(SavedItem, pk=pk, user=request.user)
    listing_title = saved_item.listing.title
    saved_item.delete()
    messages.success(request, f"Removed '{listing_title}' from your wishlist.")
    return redirect('accounts:saved_listings')


@login_required
def checkout(request):
    """
    Handles the checkout process, creating a new order from the cart safely.
    """
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.select_related('listing').all()

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty. Add items before checking out.")
        return redirect('listings:listing_list')

    if cart.has_out_of_stock_items:
        messages.error(request, "One or more items in your cart have insufficient stock. Please review your cart.")
        return redirect('listings:view_cart')

    shipping_fee = decimal.Decimal('75.00')
    subtotal = sum(item.total_price for item in cart_items)
    grand_total = subtotal + shipping_fee

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    order = form.save(commit=False)
                    order.user = request.user
                    order.shipping_fee = shipping_fee
                    order.total_price = grand_total
                    order.save()

                    listing_ids = [item.listing.id for item in cart_items]
                    listings_for_update = Listing.objects.select_for_update().filter(id__in=listing_ids)
                    listings_map = {listing.id: listing for listing in listings_for_update}

                    order_items_to_create = []
                    for item in cart_items:
                        listing = listings_map.get(item.listing.id)
                        if not listing.has_sufficient_stock(item.quantity):
                            raise ValueError(
                                f"Insufficient stock for '{listing.title}'. "
                                f"Only {listing.stock} available, but {item.quantity} were requested."
                            )

                        order_items_to_create.append(
                            OrderItem(
                                order=order,
                                listing=listing,
                                product_title=listing.title,  # Denormalize title
                                quantity=item.quantity,
                                price=listing.price
                            )
                        )
                        listing.stock -= item.quantity
                        if listing.stock == 0:
                            listing.status = 'sold'

                    OrderItem.objects.bulk_create(order_items_to_create)
                    Listing.objects.bulk_update(listings_for_update, ['stock', 'status'])

                    # Send notifications
                    sellers_to_notify = {item.listing.seller for item in cart_items}
                    for seller in sellers_to_notify:
                        Notification.objects.create(
                            recipient=seller,
                            message=f"You have a new order containing one or more of your items.",
                            notification_type='new_order',
                            link=reverse('accounts:seller_orders')
                        )

                    cart.items.all().delete()

                messages.success(request, "Your order has been placed successfully!")
                return redirect('listings:view_receipt', pk=order.pk)

            except ValueError as e:
                messages.error(request, f"Checkout failed: {e}")
                return redirect('listings:view_cart')
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
    """
    Updates the quantity of an item in the cart.
    """
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        try:
            new_quantity = int(request.POST.get('quantity'))

            with transaction.atomic():
                item_to_update = CartItem.objects.select_for_update().select_related('listing').get(pk=pk)
                listing_stock = item_to_update.listing.stock

                if new_quantity <= 0:
                    messages.info(request, f"'{item_to_update.listing.title}' was removed from your cart.")
                    item_to_update.delete()
                elif new_quantity <= listing_stock:
                    item_to_update.quantity = new_quantity
                    item_to_update.save()
                else:
                    messages.error(request,
                                   f"Cannot update quantity. Only {listing_stock} units are available for '{item_to_update.listing.title}'.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity provided.")

    return redirect('listings:view_cart')


@login_required
def seller_order_detail(request, pk):
    """
    Displays details for a specific order from the seller's perspective.
    """
    order = get_object_or_404(Order, pk=pk)
    # Use the centralized model method to check permission
    if not order.is_seller(request.user):
        raise Http404("You do not have permission to view this order's details.")

    seller_items = order.items.filter(listing__seller=request.user).select_related('listing')
    context = {
        'order': order,
        'seller_items': seller_items
    }
    return render(request, 'listings/seller_order_detail.html', context)


@login_required
def view_receipt(request, pk):
    """
    Displays the receipt for a completed order.
    """
    order = get_object_or_404(Order, pk=pk, user=request.user)
    order_items = order.items.select_related('listing').prefetch_related('listing__images').all()
    context = {
        'order': order,
        'order_items': order_items,
        'subtotal': order.total_price - order.shipping_fee,
    }
    return render(request, 'listings/receipt.html', context)


def search_suggestions(request):
    """
    Provides search suggestions for listings.
    """
    query = request.GET.get('q', '')
    data = []
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


@login_required
def view_invoice(request, pk):
    """
    Displays a seller-specific invoice for an order.
    """
    order = get_object_or_404(Order, pk=pk)
    is_buyer = order.user == request.user
    # Use the model method to check if the user is a seller for this order
    is_seller = order.is_seller(request.user)

    if not (is_buyer or is_seller):
        return HttpResponseForbidden("You are not allowed to view this invoice.")

    # Show all items if buyer, otherwise filter to seller's items
    if is_seller and not is_buyer:
        order_items = order.items.filter(listing__seller=request.user).select_related('listing').prefetch_related(
            'listing__images')
    else:
        order_items = order.items.select_related('listing').prefetch_related('listing__images')

    subtotal = sum(item.total_price for item in order_items)

    context = {
        'order': order,
        'order_items': order_items,
        'subtotal': subtotal,
        'is_seller_view': is_seller and not is_buyer,
    }
    return render(request, 'listings/invoice.html', context)