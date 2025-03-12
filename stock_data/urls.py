# stock_data/urls.py
from django.urls import path

from . import views

app_name = 'stock_data'

urlpatterns = [
    path('search/', views.search_results, name='search_results'),
    path('refresh/<str:ticker>/', views.refresh_company_data, name='refresh_data'),
    path('api/search-suggestions/', views.search_suggestions, name='search_suggestions'),
]