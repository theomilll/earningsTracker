# stock_data/admin.py
from django.contrib import admin

from .models import Company, FinancialData, SearchResult


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'name', 'sector', 'country', 'last_updated')
    search_fields = ('ticker', 'name')
    list_filter = ('sector', 'country')

@admin.register(FinancialData)
class FinancialDataAdmin(admin.ModelAdmin):
    list_display = ('company', 'market_cap', 'current_price', 'pe_ratio', 'quality_score', 'last_updated')
    search_fields = ('company__ticker', 'company__name')

@admin.register(SearchResult)
class SearchResultAdmin(admin.ModelAdmin):
    list_display = ('query', 'last_updated')
    search_fields = ('query',)