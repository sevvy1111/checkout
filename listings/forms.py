# listings/forms.py
from django import forms
from .models import Listing, Review, Order, Category


class ListingForm(forms.ModelForm):
    """
    Form for creating and updating a Listing.
    """
    # Only allow selecting categories that do not have children (leaf nodes)
    # The ordering makes the dropdown much more intuitive
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(children__isnull=True).order_by('parent__name', 'name'),
        required=True,
        empty_label="Select a Category",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'price', 'condition', 'category', 'city',
            'status', 'featured', 'latitude', 'longitude', 'stock'
        ]
        widgets = {
            'price': forms.TextInput(attrs={'placeholder': 'e.g., 1500.00', 'inputmode': 'decimal'}),
            'description': forms.Textarea(attrs={'rows': 5}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }


class ReviewForm(forms.ModelForm):
    """
    Form for creating a Review.
    """
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your review here...'}),
        }


class OrderForm(forms.ModelForm):
    """
    Form for handling the checkout process and creating an Order.
    """
    PAYMENT_CHOICES = [('COD', 'Cash on Delivery')]
    payment_method = forms.ChoiceField(
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect,
        initial='COD'
    )

    class Meta:
        model = Order
        fields = ['full_name', 'shipping_address', 'shipping_city', 'shipping_postal_code', 'gift_note', 'payment_method']
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Street, Building, etc.'}),
            'gift_note': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional: Add a personal gift note'}),
        }


class OrderStatusForm(forms.ModelForm):
    """
    Form for updating an Order's status.
    """
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'})
        }