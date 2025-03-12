# company_profiles/views.py
import json
import logging

import pandas as pd
import yfinance as yf
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from stock_data.models import Company, FinancialData
from stock_data.utils import get_company_data

logger = logging.getLogger(__name__)

def company_detail(request, ticker):
    """Display detailed company profile and financial information."""
    ticker = ticker.upper()  # Ensure ticker is uppercase
    company = get_company_data(ticker)
    
    if not company:
        # Company not found
        return render(request, 'company_profiles/company_not_found.html', {
            'ticker': ticker
        })
    
    try:
        # Get historical price data for charts
        ticker_obj = yf.Ticker(ticker)
        
        # YTD price history for chart
        hist_ytd = ticker_obj.history(period="ytd")
        price_data = []
        for date, row in hist_ytd.iterrows():
            price_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'price': round(float(row['Close']), 2)
            })
        
        # Get historical financial data for charts
        income_stmt = ticker_obj.income_stmt
        balance_sheet = ticker_obj.balance_sheet
        cash_flow = ticker_obj.cashflow
        
        # Calculate growth metrics
        financial_history = {
            'years': [col.strftime('%Y') for col in income_stmt.columns],
            'revenue': [float(income_stmt.loc['Total Revenue', col]) if 'Total Revenue' in income_stmt.index else 0 for col in income_stmt.columns],
            'ebitda': [float(income_stmt.loc['EBITDA', col]) if 'EBITDA' in income_stmt.index else 0 for col in income_stmt.columns],
            'net_income': [float(income_stmt.loc['Net Income', col]) if 'Net Income' in income_stmt.index else 0 for col in income_stmt.columns],
            'eps': [float(income_stmt.loc['Basic EPS', col]) if 'Basic EPS' in income_stmt.index else 0 for col in income_stmt.columns],
            'fcf': [float(cash_flow.loc['Free Cash Flow', col]) if 'Free Cash Flow' in cash_flow.index else 0 for col in income_stmt.columns],
            'cash': [float(balance_sheet.loc['Cash And Cash Equivalents', col]) if 'Cash And Cash Equivalents' in balance_sheet.index else 0 for col in balance_sheet.columns],
            'debt': [float(balance_sheet.loc['Total Debt', col]) if 'Total Debt' in balance_sheet.index else 0 for col in balance_sheet.columns],
        }
        
        # Get dividend history
        dividends = ticker_obj.dividends
        dividend_data = []
        for date, value in dividends.items():
            dividend_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'dividend': float(value)
            })
        
        # Peers comparison
        peers = ticker_obj.info.get('companyOfficers', [])[:5]  # Use a different field as needed
        # In a real implementation, you'd get actual peers
        
        return render(request, 'company_profiles/company_detail.html', {
            'company': company,
            'financial_history': json.dumps(financial_history),
            'price_data': json.dumps(price_data),
            'dividend_data': json.dumps(dividend_data),
            'peers': peers,
        })
        
    except Exception as e:
        logger.error(f"Error rendering company detail for {ticker}: {e}")
        # Still show the company page but with error message
        return render(request, 'company_profiles/company_detail.html', {
            'company': company,
            'error': str(e)
        })

def company_financials(request, ticker):
    """Display detailed financial statements for a company."""
    ticker = ticker.upper()
    company = get_company_data(ticker)
    
    if not company:
        return redirect('core:home')
    
    try:
        ticker_obj = yf.Ticker(ticker)
        
        income_stmt = ticker_obj.income_stmt.fillna(0)
        balance_sheet = ticker_obj.balance_sheet.fillna(0)
        cash_flow = ticker_obj.cashflow.fillna(0)
        
        # Format financial statements for template
        income_data = []
        for index, row in income_stmt.iterrows():
            income_data.append({
                'item': index,
                'values': [{'year': col.strftime('%Y'), 'value': f"{row[col]:,.0f}"} for col in income_stmt.columns]
            })
        
        balance_data = []
        for index, row in balance_sheet.iterrows():
            balance_data.append({
                'item': index,
                'values': [{'year': col.strftime('%Y'), 'value': f"{row[col]:,.0f}"} for col in balance_sheet.columns]
            })
        
        cashflow_data = []
        for index, row in cash_flow.iterrows():
            cashflow_data.append({
                'item': index,
                'values': [{'year': col.strftime('%Y'), 'value': f"{row[col]:,.0f}"} for col in cash_flow.columns]
            })
        
        return render(request, 'company_profiles/financial_statements.html', {
            'company': company,
            'income_data': income_data,
            'balance_data': balance_data,
            'cashflow_data': cashflow_data,
        })
        
    except Exception as e:
        logger.error(f"Error fetching financial statements for {ticker}: {e}")
        return render(request, 'company_profiles/financial_statements.html', {
            'company': company,
            'error': f"Could not load financial statements: {str(e)}"
        })

def company_peers(request, ticker):
    """Compare company with its peers."""
    ticker = ticker.upper()
    company = get_company_data(ticker)
    
    if not company:
        return redirect('core:home')
    
    try:
        ticker_obj = yf.Ticker(ticker)
        
        # Get sector/industry peers
        sector = company.sector
        industry = company.industry
        
        if sector:
            # In a real implementation, you would query companies with the same sector
            # Here's a simple mockup
            peer_tickers = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN']
            peers = []
            
            for peer_ticker in peer_tickers:
                if peer_ticker != ticker:
                    peer_company = get_company_data(peer_ticker)
                    if peer_company:
                        peers.append(peer_company)
            
            # Prepare comparison metrics
            metrics = [
                {'name': 'Market Cap', 'field': 'market_cap', 'formatter': lambda x: f"${x:,.0f}" if x else "N/A"},
                {'name': 'P/E Ratio', 'field': 'pe_ratio', 'formatter': lambda x: f"{x:.2f}" if x else "N/A"},
                {'name': 'P/S Ratio', 'field': 'ps_ratio', 'formatter': lambda x: f"{x:.2f}" if x else "N/A"},
                {'name': 'EV/EBITDA', 'field': 'ev_ebitda', 'formatter': lambda x: f"{x:.2f}" if x else "N/A"},
                {'name': 'Profit Margin', 'field': 'profit_margin', 'formatter': lambda x: f"{x:.2f}%" if x else "N/A"},
                {'name': 'Dividend Yield', 'field': 'dividend_yield', 'formatter': lambda x: f"{x:.2f}%" if x else "N/A"},
            ]
            
            comparison_data = []
            for metric in metrics:
                row = {'metric': metric['name']}
                
                # Get value for the main company
                if hasattr(company, 'financials'):
                    main_value = getattr(company.financials, metric['field'], None)
                    row['main'] = metric['formatter'](main_value) if main_value is not None else "N/A"
                else:
                    row['main'] = "N/A"
                
                # Get values for peer companies
                for peer in peers:
                    if hasattr(peer, 'financials'):
                        peer_value = getattr(peer.financials, metric['field'], None)
                        row[peer.ticker] = metric['formatter'](peer_value) if peer_value is not None else "N/A"
                    else:
                        row[peer.ticker] = "N/A"
                
                comparison_data.append(row)
            
            return render(request, 'company_profiles/company_peers.html', {
                'company': company,
                'peers': peers,
                'comparison_data': comparison_data,
            })
        else:
            return render(request, 'company_profiles/company_peers.html', {
                'company': company,
                'error': "Sector information not available for peer comparison."
            })
            
    except Exception as e:
        logger.error(f"Error comparing peers for {ticker}: {e}")
        return render(request, 'company_profiles/company_peers.html', {
            'company': company,
            'error': f"Could not load peer comparison: {str(e)}"
        })

def company_news(request, ticker):
    """Display latest news for a company."""
    ticker = ticker.upper()
    company = get_company_data(ticker)
    
    if not company:
        return redirect('core:home')
    
    try:
        # For a real implementation, you'd use a news API
        # Here's a mockup
        news_items = [
            {
                'title': f"{company.name} Reports Strong Quarterly Results",
                'source': "Market News",
                'date': "2025-03-01",
                'url': "#",
                'summary': f"Lorem ipsum dolor sit amet, consectetur adipiscing elit. {company.name} announced better than expected quarterly results."
            },
            {
                'title': f"Analysts Upgrade {company.name} Stock",
                'source': "Financial Times",
                'date': "2025-02-28",
                'url': "#",
                'summary': f"Several analysts have upgraded {company.name} following positive earnings and growth outlook."
            },
            {
                'title': f"{company.name} Expands Into New Markets",
                'source': "Business Weekly",
                'date': "2025-02-25",
                'url': "#",
                'summary': f"{company.name} announced plans to expand operations into new global markets, citing strong demand."
            },
        ]
        
        return render(request, 'company_profiles/company_news.html', {
            'company': company,
            'news_items': news_items,
        })
        
    except Exception as e:
        logger.error(f"Error fetching news for {ticker}: {e}")
        return render(request, 'company_profiles/company_news.html', {
            'company': company,
            'error': f"Could not load news: {str(e)}"
        })