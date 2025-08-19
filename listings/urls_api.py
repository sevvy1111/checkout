# listings/urls_api.py
from django.urls import path
from . import views

app_name = 'listings_api'

urlpatterns = [
    # URL for toggling the saved/wishlist status of a listing
    path('listing/<int:pk>/toggle-save/', views.toggle_save_listing, name='toggle_save_listing'),
    # URL for AJAX-based filtering of listings
    path('filter-listings/', views.filter_listings, name='filter_listings'),
]