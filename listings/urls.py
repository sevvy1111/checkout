# listings/urls.py
from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    path('', views.ListingListView.as_view(), name='listing_list'),
    path('listing/create/', views.ListingCreateView.as_view(), name='listing_create'),
    path('listing/<int:pk>/', views.ListingDetailView.as_view(), name='listing_detail'),
    path('listing/<int:pk>/update/', views.ListingUpdateView.as_view(), name='listing_update'),
    path('listing/<int:pk>/save/', views.toggle_save_listing, name='listing_save_toggle'),
    path('api/filter-listings/', views.filter_listings, name='filter_listings'),

    # New URL for marking a listing as sold
    path('listing/<int:pk>/mark-sold/', views.mark_listing_as_sold, name='mark_as_sold'),

    # New URL for the shopping cart
    path('listing/<int:pk>/add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:pk>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
]