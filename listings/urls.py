# listings/urls.py
from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    path('', views.ListingListView.as_view(), name='listing_list'),
    path('listing/create/', views.ListingCreateView.as_view(), name='listing_create'),
    path('listing/<int:pk>/', views.ListingDetailView.as_view(), name='listing_detail'),
    path('listing/<int:pk>/update/', views.ListingUpdateView.as_view(), name='listing_update'),
    path('listing/<int:pk>/delete/', views.ListingDeleteView.as_view(), name='listing_delete'),
    path('listing/<int:pk>/sold/', views.mark_listing_as_sold, name='mark_listing_as_sold'),
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/<int:pk>/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.view_cart, name='view_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('receipt/<int:pk>/', views.view_receipt, name='view_receipt'),
    path('seller/order/<int:pk>/', views.seller_order_detail, name='seller_order_detail'),
    path('invoice/<int:pk>/', views.view_invoice, name='view_invoice'),
    path('saved/remove/<int:pk>/', views.remove_from_saved, name='remove_from_saved'),
]