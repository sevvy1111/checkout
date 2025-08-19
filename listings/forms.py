# listings/forms.py
from django import forms
from .models import Listing, Review, Order, Category
from .filters import PHILIPPINE_CITIES

class ListingForm(forms.ModelForm):
    city = forms.ChoiceField(
        choices=PHILIPPINE_CITIES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True,
        empty_label="Select a Category",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'price', 'category', 'city',
            'status', 'featured', 'latitude', 'longitude', 'stock'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your review here...'}),
        }

class OrderForm(forms.ModelForm):
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

# FIX: Created a new form for updating order status, bound to the Order model.
class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select form-select-sm'})
        }