# marketplace/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# Define API patterns separately for better organization
api_urlpatterns = [
    path('', include('listings.urls_api', namespace='listings_api')),
]

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/', include(api_urlpatterns)),

    # Main apps
    path('', include('listings.urls', namespace='listings')),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('messages/', include(('messaging.urls', 'messaging'), namespace='messaging')),
    path('notifications/', include('notifications.urls', namespace='notifications')),

    # --- Corrected Authentication URLs ---
    # We explicitly define the paths here to point to our custom template locations.
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(template_name='accounts/login.html'),
        name='login'
    ),
    path(
        'accounts/logout/',
        auth_views.LogoutView.as_view(template_name='registration/logged_out.html'),
        name='logout'
    ),
    path(
        'accounts/password_reset/',
        auth_views.PasswordResetView.as_view(template_name='accounts/password_reset_form.html'),
        name='password_reset'
    ),
    path(
        'accounts/password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
        name='password_reset_done'
    ),
    path(
        'accounts/reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
        name='password_reset_confirm'
    ),
    path(
        'accounts/reset/done/',
        auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
        name='password_reset_complete'
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)