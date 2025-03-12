from django.shortcuts import redirect, render


def home(request):
    """Homepage with search functionality."""
    return render(request, 'core/home.html')

def search(request):
    """Handle search for company names/tickers."""
    query = request.GET.get('query', '').strip()
    
    if not query:
        return redirect('core:home')
    
    # Check if query is a ticker (all uppercase)
    if query.isupper() and len(query) <= 5:
        # Redirect to company profile page
        return redirect('company_profiles:detail', ticker=query)
    
    # Otherwise, treat as company name search
    # This will be implemented in the stock_data app
    return redirect('stock_data:search_results', query=query)