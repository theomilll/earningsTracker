# stock_data/views.py
import json
import logging

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import Company, FinancialData, SearchResult
from .utils import fetch_company_info, fetch_financial_data, search_companies

logger = logging.getLogger(__name__)

def search_results(request):
    """Display search results for company name queries."""
    query = request.GET.get('query', '').strip()
    
    if not query:
        return redirect('core:home')
    
    # Check for cached search results
    cached_search = SearchResult.objects.filter(query__iexact=query).first()
    
    if cached_search and not cached_search.is_stale():
        # Use cached results
        results = json.loads(cached_search.results_json)
    else:
        # Perform new search
        results = search_companies(query)
        
        # Cache the results
        if results:
            if cached_search:
                cached_search.results_json = json.dumps(results)
                cached_search.last_updated = timezone.now()
                cached_search.save()
            else:
                SearchResult.objects.create(
                    query=query,
                    results_json=json.dumps(results),
                )
    
    return render(request, 'stock_data/search_results.html', {
        'query': query,
        'results': results,
    })

def refresh_company_data(request, ticker):
    """Force refresh company data from yfinance."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    company = get_object_or_404(Company, ticker=ticker)
    
    # Fetch fresh company information
    company_info = fetch_company_info(ticker)
    if company_info:
        for key, value in company_info.items():
            if key != 'ticker' and hasattr(company, key):
                setattr(company, key, value)
        company.last_updated = timezone.now()
        company.save()
    
    # Fetch fresh financial data
    financial_data = fetch_financial_data(ticker)
    if financial_data:
        financials, created = FinancialData.objects.get_or_create(company=company)
        
        for key, value in financial_data.items():
            if hasattr(financials, key):
                setattr(financials, key, value)
        
        financials.last_updated = timezone.now()
        financials.save()
    
    return JsonResponse({'status': 'success', 'message': f'Data for {ticker} refreshed successfully'})

def get_company_data(ticker):
    """Get or create company data for the given ticker."""
    # Try to get existing company
    company = Company.objects.filter(ticker=ticker).first()
    
    if not company:
        # Fetch company info from yfinance
        company_info = fetch_company_info(ticker)
        if not company_info:
            return None
        
        # Create new company record
        company = Company.objects.create(**company_info)
    elif company.is_stale():
        # Update stale company info
        company_info = fetch_company_info(ticker)
        if company_info:
            for key, value in company_info.items():
                if key != 'ticker' and hasattr(company, key):
                    setattr(company, key, value)
            company.last_updated = timezone.now()
            company.save()
    
    # Get or create financial data
    financials = FinancialData.objects.filter(company=company).first()
    
    if not financials or (timezone.now() - financials.last_updated).days > 1:
        # Fetch or update financial data
        financial_data = fetch_financial_data(ticker)
        if financial_data:
            if not financials:
                financials = FinancialData.objects.create(company=company, **financial_data)
            else:
                for key, value in financial_data.items():
                    if hasattr(financials, key):
                        setattr(financials, key, value)
                financials.last_updated = timezone.now()
                financials.save()
    
    return company

# stock_data/views.py
def search_suggestions(request):
    """Return JSON suggestions for search autocomplete."""
    query = request.GET.get('query', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    # Check cache for suggestions
    cached_search = SearchResult.objects.filter(query__iexact=query).first()
    
    if cached_search and not cached_search.is_stale():
        # Use cached results
        suggestions = json.loads(cached_search.results_json)
    else:
        # Perform new search
        suggestions = search_companies(query)
        
        # Cache the results
        if suggestions:
            if cached_search:
                cached_search.results_json = json.dumps(suggestions)
                cached_search.last_updated = timezone.now()
                cached_search.save()
            else:
                SearchResult.objects.create(
                    query=query,
                    results_json=json.dumps(suggestions),
                )
    
    return JsonResponse({'suggestions': suggestions})