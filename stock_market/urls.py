# stock_market/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('stock/', include('stock_data.urls')),
    path('company/', include('company_profiles.urls')),
    path('charts/', include('charts.urls')),
]