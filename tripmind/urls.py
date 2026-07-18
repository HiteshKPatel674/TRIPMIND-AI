"""
URL configuration for tripmind project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('auth/', include('django.contrib.auth.urls')),
]

handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'
