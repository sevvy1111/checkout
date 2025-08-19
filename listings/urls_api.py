# listings/urls_api.py
from django.urls import path
from . import views

app_name = 'listings_api'

urlpatterns = [
    path('listing/<int:pk>/toggle-save/', views.toggle_save_listing, name='toggle_save_listing'),
    path('filter-listings/', views.filter_listings, name='filter_listings'),
    # FIX: Added new URL for search suggestions
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),
]