# marketplace/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Accounts: signup/profile (your app)
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    # Django auth (login, password reset, ... )
    path('accounts/', include('django.contrib.auth.urls')),
    # Main listings app
    path('', include('listings.urls', namespace='listings')),
    # Messaging app
    path('msgs/', include(('messaging.urls', 'messaging'), namespace='messaging')),
    # Notifications app
    path('notifications/', include('notifications.urls', namespace='notifications')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)# marketplace/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Accounts: signup/profile (your app)
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    # Django auth (login, password reset, ... )
    path('accounts/', include('django.contrib.auth.urls')),
    # Main listings app
    path('', include('listings.urls', namespace='listings')),
    # Messaging app
    path('msgs/', include(('messaging.urls', 'messaging'), namespace='messaging')),
    # Notifications app
    path('notifications/', include('notifications.urls', namespace='notifications')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)