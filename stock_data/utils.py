# stock_data/utils.py
import json
import logging
from datetime import datetime
from decimal import Decimal

import pandas as pd
import yfinance as yf
from django.utils import timezone

logger = logging.getLogger(__name__)

def fetch_company_info(ticker):
    """Fetch basic company information from yfinance."""
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        return {
            'ticker': ticker,
            'name': info.get('longName', ticker),
            'sector': info.get('sector'),
            'industry': info.get('industry'),
            'country': info.get('country'),
            'website': info.get('website'),
            'logo_url': info.get('logo_url'),
        }
    except Exception as e:
        logger.error(f"Error fetching company info for {ticker}: {e}")
        return None

def fetch_financial_data(ticker):
    """Fetch and calculate financial metrics for a company."""
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        # Get financial statements
        income_stmt = ticker_obj.income_stmt
        balance_sheet = ticker_obj.balance_sheet
        cash_flow = ticker_obj.cashflow
        
        # Calculate YTD price change
        hist = ticker_obj.history(period="ytd")
        if not hist.empty:
            start_price = hist.iloc[0]['Close']
            current_price = info.get('currentPrice', hist.iloc[-1]['Close'])
            price_change_ytd = ((current_price - start_price) / start_price) * 100
        else:
            price_change_ytd = None
        
        # Calculate EV/EBITDA
        market_cap = info.get('marketCap')
        total_debt = balance_sheet.loc['Total Debt', balance_sheet.columns[0]] if 'Total Debt' in balance_sheet.index else 0
        cash = balance_sheet.loc['Cash And Cash Equivalents', balance_sheet.columns[0]] if 'Cash And Cash Equivalents' in balance_sheet.index else 0
        ebitda = income_stmt.loc['EBITDA', income_stmt.columns[0]] if 'EBITDA' in income_stmt.index else 0
        
        ev = market_cap + total_debt - cash if market_cap else None
        ev_ebitda = (ev / ebitda) if ev and ebitda and ebitda > 0 else None
        
        # Calculate FCF Yield
        fcf = cash_flow.loc['Free Cash Flow', cash_flow.columns[0]] if 'Free Cash Flow' in cash_flow.index else None
        fcf_yield = (fcf / market_cap * 100) if fcf and market_cap and market_cap > 0 else None
        
        # Calculate Piotroski Score
        quality_score = calculate_piotroski_score(income_stmt, balance_sheet, cash_flow)
        
        # Get dividend info
        dividends = ticker_obj.dividends
        if not dividends.empty:
            div_yield = info.get('dividendYield', 0) * 100  # Convert to percentage
            payout = info.get('payoutRatio', 0) * 100  # Convert to percentage
            ex_date = info.get('exDividendDate')
            if ex_date:
                ex_date = datetime.fromtimestamp(ex_date)
        else:
            div_yield = 0
            payout = 0
            ex_date = None
        
        return {
            'market_cap': market_cap,
            'current_price': info.get('currentPrice'),
            'price_change_ytd': price_change_ytd,
            'pe_ratio': info.get('trailingPE'),
            'ps_ratio': info.get('priceToSalesTrailing12Months'),
            'pb_ratio': info.get('priceToBook'),
            'ev_ebitda': ev_ebitda,
            'fcf_yield': fcf_yield,
            'quality_score': quality_score,
            'profit_margin': info.get('profitMargins', 0) * 100,  # Convert to percentage
            'operating_margin': info.get('operatingMargins', 0) * 100,  # Convert to percentage
            'cash': cash,
            'total_debt': total_debt,
            'net_cash': cash - total_debt,
            'shares_outstanding': info.get('sharesOutstanding'),
            'dividend_yield': div_yield,
            'payout_ratio': payout,
            'ex_dividend_date': ex_date,
        }
    except Exception as e:
        logger.error(f"Error fetching financial data for {ticker}: {e}")
        return None

def calculate_piotroski_score(income_stmt, balance_sheet, cash_flow):
    """Calculate Piotroski F-Score (0-9) based on financial statements."""
    score = 0
    
    try:
        # Get the most recent and previous year data
        current_year = income_stmt.columns[0]
        prev_year = income_stmt.columns[1] if len(income_stmt.columns) > 1 else None
        
        if prev_year:
            # 1. Positive Net Income
            if income_stmt.loc['Net Income', current_year] > 0:
                score += 1
                
            # 2. Positive ROA
            current_assets = balance_sheet.loc['Total Assets', current_year]
            if current_assets > 0 and income_stmt.loc['Net Income', current_year] / current_assets > 0:
                score += 1
                
            # 3. Positive Operating Cash Flow
            if cash_flow.loc['Operating Cash Flow', current_year] > 0:
                score += 1
                
            # 4. OCF > Net Income
            if cash_flow.loc['Operating Cash Flow', current_year] > income_stmt.loc['Net Income', current_year]:
                score += 1
                
            # 5. Decreasing Long Term Debt ratio
            prev_assets = balance_sheet.loc['Total Assets', prev_year]
            current_debt = balance_sheet.loc['Long Term Debt', current_year] if 'Long Term Debt' in balance_sheet.index else 0
            prev_debt = balance_sheet.loc['Long Term Debt', prev_year] if 'Long Term Debt' in balance_sheet.index else 0
            
            if (current_debt / current_assets) < (prev_debt / prev_assets):
                score += 1
                
            # 6. Increasing Current Ratio
            current_current_assets = balance_sheet.loc['Current Assets', current_year] if 'Current Assets' in balance_sheet.index else 0
            current_current_liab = balance_sheet.loc['Current Liabilities', current_year] if 'Current Liabilities' in balance_sheet.index else 1
            prev_current_assets = balance_sheet.loc['Current Assets', prev_year] if 'Current Assets' in balance_sheet.index else 0
            prev_current_liab = balance_sheet.loc['Current Liabilities', prev_year] if 'Current Liabilities' in balance_sheet.index else 1
            
            current_ratio = current_current_assets / current_current_liab if current_current_liab else 0
            prev_ratio = prev_current_assets / prev_current_liab if prev_current_liab else 0
            
            if current_ratio > prev_ratio:
                score += 1
                
            # 7. No New Shares Issued
            current_shares = balance_sheet.loc['Common Stock', current_year] if 'Common Stock' in balance_sheet.index else 0
            prev_shares = balance_sheet.loc['Common Stock', prev_year] if 'Common Stock' in balance_sheet.index else 0
            
            if current_shares <= prev_shares:
                score += 1
                
            # 8. Increasing Gross Margin
            current_gross = income_stmt.loc['Gross Profit', current_year] / income_stmt.loc['Total Revenue', current_year] if 'Gross Profit' in income_stmt.index and income_stmt.loc['Total Revenue', current_year] else 0
            prev_gross = income_stmt.loc['Gross Profit', prev_year] / income_stmt.loc['Total Revenue', prev_year] if 'Gross Profit' in income_stmt.index and income_stmt.loc['Total Revenue', prev_year] else 0
            
            if current_gross > prev_gross:
                score += 1
                
            # 9. Increasing Asset Turnover
            current_turnover = income_stmt.loc['Total Revenue', current_year] / current_assets if current_assets else 0
            prev_turnover = income_stmt.loc['Total Revenue', prev_year] / prev_assets if prev_assets else 0
            
            if current_turnover > prev_turnover:
                score += 1
    
    except Exception as e:
        logger.error(f"Error calculating Piotroski score: {e}")
        # Return 0 or a default value on error
        return 0
        
    return score

def search_companies(query):
    """Search for companies by name or partial ticker using yfinance."""
    try:
        # Search using yfinance's search functionality
        search_results = yf.Ticker(query).search()
        
        if not search_results:
            # Try using tickers module for common companies
            from yahoo_fin import stock_info
            tickers = stock_info.tickers_sp500() + stock_info.tickers_nasdaq() + stock_info.tickers_dow()
            
            # Filter tickers that contain the query (case insensitive)
            matches = [t for t in tickers if query.lower() in t.lower()]
            
            results = []
            for match in matches[:10]:  # Limit to 10 results
                try:
                    info = yf.Ticker(match).info
                    results.append({
                        'ticker': match,
                        'name': info.get('longName', match),
                        'exchange': info.get('exchange', ''),
                    })
                except:
                    pass
            
            return results
        
        # Process yfinance search results
        results = []
        for item in search_results[:10]:  # Limit to 10 results
            results.append({
                'ticker': item.get('symbol'),
                'name': item.get('shortname', item.get('longname', item.get('symbol'))),
                'exchange': item.get('exchange', ''),
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching for companies with query '{query}': {e}")
        return []
    
def get_company_data(ticker):
    """Get or create company data for the given ticker."""
    from django.utils import timezone
    from stock_data.models import Company, FinancialData

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