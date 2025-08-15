# listings/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import Listing, ListingImage, Review

# Import the same comprehensive lists
from .filters import PHILIPPINE_CITIES, MARKETPLACE_CATEGORIES

class ListingForm(forms.ModelForm):
    # Use ChoiceField for dropdowns populated with our comprehensive lists
    city = forms.ChoiceField(choices=PHILIPPINE_CITIES, required=True, widget=forms.Select(attrs={'class': 'form-select'}))
    category = forms.ChoiceField(choices=MARKETPLACE_CATEGORIES, required=True, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Listing
        # Ensure all relevant fields are included
        fields = ['title', 'description', 'price', 'category', 'city', 'status', 'featured', 'latitude', 'longitude', 'stock']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'latitude': forms.HiddenInput(),
            'longitude': forms.HiddenInput(),
        }

ListingImageFormset = inlineformset_factory(
    Listing,
    ListingImage,
    fields=['image'],
    extra=6,
    can_delete=True
)

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-select'}),
            'comment': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your review here...'}),
        }