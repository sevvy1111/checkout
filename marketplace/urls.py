# marketplace/urls.py

from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Accounts: signup/profile (your app)
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Django auth (login, password reset, ... )
    path('accounts/', include('django.contrib.auth.urls')),

    # Custom logout: POST -> redirect to listings home (prevents Django admin-style page)
    path(
        'accounts/logout/',
        auth_views.LogoutView.as_view(next_page=reverse_lazy('listings:listing_list')),
        name='logout'
    ),

    # Main listings app
    path('', include('listings.urls', namespace='listings')),

    # Messaging app
    path('msgs/', include(('messaging.urls', 'messaging'), namespace='messaging')),
]

# The `static()` function is for local development only.
# It is explicitly removed in production settings where DEBUG=False.
# Media files are now handled by Cloudinary.