from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve

urlpatterns = [
    path('alamana-admin/', admin.site.urls),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('', include('repairs.urls')),

    # Force media files to be served by Django even when DEBUG=False.
    # NOTE: This is inefficient and not recommended for a real production site.
    # For production, a web server (e.g., Nginx) should be configured
    # to serve files from the MEDIA_ROOT directory directly.
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

# Customize admin site
admin.site.site_header = "Alamana Jo - Repair Management"
admin.site.site_title = "Alamana Jo Admin"
admin.site.index_title = "E-Bike Repair Job Management"
