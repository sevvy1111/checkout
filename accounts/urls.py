# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/<str:username>/', views.public_profile_view, name='public_profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('saved/', views.saved_listings_view, name='saved_listings'),
    path('order-history/', views.order_history_view, name='order_history'),
    path('seller-orders/', views.seller_orders_view, name='seller_orders'),

    # New URLs for phone verification
    path('verify-phone/', views.verify_phone_view, name='verify_phone'),
    path('send-verification-code/', views.send_verification_code_view, name='send_verification_code'),

    # Auth URLs
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    # ... (rest of the auth URLs) ...
]