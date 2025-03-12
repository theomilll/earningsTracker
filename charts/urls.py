# charts/urls.py
from django.urls import path

from . import views

app_name = 'charts'

urlpatterns = [
    # Stock price chart
    path('price/<str:ticker>/', views.stock_price_chart, name='stock_price'),
    path('api/price/<str:ticker>/', views.price_data_json, name='price_data'),
    
    # Financial metrics chart
    path('financials/<str:ticker>/', views.financial_chart, name='financial'),
    path('api/financials/<str:ticker>/', views.financial_data_json, name='financial_data'),
    
    # Company comparison chart
    path('comparison/', views.comparison_chart, name='comparison'),
    path('api/comparison/', views.comparison_data_json, name='comparison_data'),
    
    # Technical analysis chart
    path('technical/<str:ticker>/', views.technical_chart, name='technical'),
    path('api/technical/<str:ticker>/', views.technical_data_json, name='technical_data'),
]