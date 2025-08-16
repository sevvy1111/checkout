# listings/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Sum, F, Avg

from .models import Listing, ListingImage, SavedItem, Review, Cart, CartItem, Checkout
from .forms import ListingForm, ReviewForm, CheckoutForm, OrderStatusForm
from .filters import ListingFilter


class ListingListView(ListView):
    model = Listing
    template_name = 'listings/listing_list.html'
    context_object_name = 'listings'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        # Corrected: Removed 'category' from select_related as it is no longer a ForeignKey
        self.filterset = ListingFilter(self.request.GET, queryset=queryset.select_related('seller').annotate(
            average_rating=Avg('reviews__rating')
        ))
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reviews'] = self.object.reviews.all().select_related('author__profile')
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
            review = form.save(commit=False)
            review.listing = self.object
            review.author = request.user
            review.save()
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

    def form_valid(self, form):
        messages.success(self.request, f"The listing '{self.object.title}' has been successfully deleted.")
        return super().form_valid(form)


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
    # Corrected: Removed 'category' from select_related
    filter = ListingFilter(request.GET, queryset=Listing.objects.all().select_related('seller').annotate(
        average_rating=Avg('reviews__rating')
    ))
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
        listing.status = 'sold'
        listing.stock = 0  # Set stock to 0 when marked as sold
        listing.save()
        return redirect('accounts:dashboard')

    return redirect('accounts:dashboard')


@login_required
def add_to_cart(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    cart, created = Cart.objects.get_or_create(user=request.user)

    if listing.stock <= 0:
        messages.error(request, f"Sorry, '{listing.title}' is currently out of stock.")
        return redirect('listings:listing_detail', pk=listing.pk)

    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, listing=listing)

    if not item_created:
        if cart_item.quantity < listing.stock:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"Added another '{listing.title}' to your cart.")
        else:
            messages.error(request, f"You have reached the maximum stock available for '{listing.title}'.")
    else:
        messages.success(request, f"Added '{listing.title}' to your cart.")

    return redirect('listings:listing_detail', pk=listing.pk)


@login_required
def view_cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'listings/cart_detail.html', {'cart': cart})


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

    if request.method == 'POST':
        checkout_form = CheckoutForm(request.POST)
        if checkout_form.is_valid():
            with transaction.atomic():
                for item in cart_items:
                    listing = item.listing
                    if listing.stock >= item.quantity:
                        listing.stock -= item.quantity
                        if listing.stock == 0:
                            listing.status = 'sold'
                        listing.save()

                        # Create a single Checkout object with all the form data
                        checkout_instance = checkout_form.save(commit=False)
                        checkout_instance.user = request.user
                        checkout_instance.listing = listing
                        checkout_instance.quantity = item.quantity
                        checkout_instance.save()

                        item.delete()
                    else:
                        messages.error(request, f"Checkout failed: Insufficient stock for '{listing.title}'.")
                        return redirect('listings:view_cart')

                messages.success(request, "Your order has been placed successfully!")
                return redirect('accounts:dashboard')
        else:
            # If the form is invalid, re-render the checkout page with errors
            return render(request, 'listings/checkout.html',
                          {'cart_items': cart_items, 'form': checkout_form, 'total_price': total_price})

    else:
        checkout_form = CheckoutForm()

    return render(request, 'listings/checkout.html',
                  {'cart_items': cart_items, 'form': checkout_form, 'total_price': total_price})


@login_required
def update_cart_item(request, pk):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        try:
            new_quantity = int(request.POST.get('quantity'))
            if new_quantity <= 0:
                cart_item.delete()
                messages.info(request, f"'{cart_item.listing.title}' was removed from your cart.")
            elif new_quantity <= cart_item.listing.stock:
                cart_item.quantity = new_quantity
                cart_item.save()
                messages.success(request, f"Quantity for '{cart_item.listing.title}' updated.")
            else:
                messages.error(request,
                               f"Cannot update quantity. Only {cart_item.listing.stock} stocks are available for '{cart_item.listing.title}'.")
        except (ValueError, TypeError):
            messages.error(request, "Invalid quantity.")

    return redirect('listings:view_cart')