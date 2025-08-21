# listings/filters.py
import django_filters
from django import forms
from django.db.models.functions import Sin, Cos, ACos, Radians

from .models import Listing, Category

CONDITION_CHOICES = [
    ('NEW', 'New'),
    ('USED', 'Used'),
]


class ListingFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        field_name='title',
        lookup_expr='icontains',
        label='Search',
        widget=forms.TextInput(attrs={'placeholder': 'Search by title...'})
    )

    category = django_filters.ChoiceFilter(
        field_name='category__name',
        lookup_expr='exact',
        label='Category',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    city = django_filters.ChoiceFilter(
        label='City',
        choices=[],
        widget=forms.Select
    )

    min_price = django_filters.NumberFilter(
        field_name="price", lookup_expr='gte', label="Min Price",
        widget=forms.TextInput(attrs={'placeholder': '₱ min', 'inputmode': 'decimal'})
    )

    max_price = django_filters.NumberFilter(
        field_name="price", lookup_expr='lte', label="Max Price",
        widget=forms.TextInput(attrs={'placeholder': '₱ max', 'inputmode': 'decimal'})
    )

    condition = django_filters.ChoiceFilter(
        choices=CONDITION_CHOICES,
        label="Condition",
        empty_label="Any Condition",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    ordering = django_filters.OrderingFilter(
        choices=(
            ('-created', 'Newest First'),
            ('price', 'Price: Low to High'),
            ('-price', 'Price: High to Low'),
        ),
        label="Sort By",
        empty_label="Default",
        widget=forms.Select
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # City choices (unchanged)
        city_choices = Listing.objects.filter(
            status='available'
        ).values_list(
            'city', 'city'
        ).distinct().order_by('city')
        self.filters['city'].extra['choices'] = [('', 'Any City')] + list(city_choices)

        # Dynamically build hierarchical category choices for the dropdown
        # CORRECTED: Added .order_by('name') to ensure parent categories are alphabetical
        parent_categories = Category.objects.filter(parent__isnull=True).order_by('name').prefetch_related('children')
        category_choices = [('', 'All Categories')]
        for parent in parent_categories:
            # The children will be ordered by the model's Meta.ordering by default
            child_choices = [(child.name, child.name) for child in parent.children.all()]
            if child_choices:
                category_choices.append((parent.name, child_choices))
        self.filters['category'].extra['choices'] = category_choices

        # Apply CSS classes
        self.filters['city'].field.widget.attrs.update({'class': 'form-select'})
        self.filters['ordering'].field.widget.attrs.update({'class': 'form-select'})

    class Meta:
        model = Listing
        fields = []