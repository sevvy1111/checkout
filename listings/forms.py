# listings/forms.py
from django import forms
from .models import Listing, ListingImage, Review, Checkout

# Import the same comprehensive lists
from .filters import PHILIPPINE_CITIES, MARKETPLACE_CATEGORIES


class ListingForm(forms.ModelForm):
    # Use ChoiceField for dropdowns populated with our comprehensive lists
    city = forms.ChoiceField(choices=PHILIPPINE_CITIES, required=True,
                             widget=forms.Select(attrs={'class': 'form-select'}))
    category = forms.ChoiceField(choices=MARKETPLACE_CATEGORIES, required=True,
                                 widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Listing
        # Ensure all relevant fields are included
        fields = ['title', 'description', 'price', 'category', 'city', 'status', 'featured', 'latitude', 'longitude',
                  'stock']
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


# --- New Checkout Form ---
class CheckoutForm(forms.ModelForm):
    # bug: The value from the form in checkout.html is 'COD', not 'cod'. Updated to match.
    PAYMENT_CHOICES = [
        ('COD', 'Cash on Delivery'),
        # Add more payment options here in the future
    ]
    payment_method = forms.ChoiceField(choices=PAYMENT_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = Checkout
        fields = ['full_name', 'shipping_address', 'shipping_city', 'shipping_postal_code', 'gift_note']
        widgets = {
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
            'gift_note': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional: Add a personal gift note'}),
        }


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Checkout
        fields = ['status']