# company_profiles/urls.py
from django.urls import path

from . import views

app_name = 'company_profiles'

urlpatterns = [
    path('<str:ticker>/', views.company_detail, name='detail'),
    path('<str:ticker>/financials/', views.company_financials, name='financials'),
    path('<str:ticker>/peers/', views.company_peers, name='peers'),
    path('<str:ticker>/news/', views.company_news, name='news'),
]