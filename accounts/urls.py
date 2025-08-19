# accounts/urls.py
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('wishlist/', views.saved_listings, name='saved_listings'),
    path('purchases/', views.order_history, name='order_history'),
    path('sales/', views.seller_orders, name='seller_orders'),
    path('user/<str:username>/', views.PublicProfileDetailView.as_view(), name='public_profile'),
    # FIX: Added the URL pattern for updating order status
    path('order/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
]