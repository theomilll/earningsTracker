# charts/views.py
import json
import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from django.http import JsonResponse
from django.shortcuts import render
from stock_data.utils import get_company_data

logger = logging.getLogger(__name__)

def stock_price_chart(request, ticker):
    """Render a page with interactive stock price chart."""
    ticker = ticker.upper()
    company = get_company_data(ticker)
    
    if not company:
        return JsonResponse({'error': 'Company not found'}, status=404)
    
    # Default time ranges for chart
    ranges = [
        {'label': '1D', 'value': '1d', 'interval': '5m'},
        {'label': '5D', 'value': '5d', 'interval': '15m'},
        {'label': '1M', 'value': '1mo', 'interval': '1d'},
        {'label': '6M', 'value': '6mo', 'interval': '1d'},
        {'label': 'YTD', 'value': 'ytd', 'interval': '1d'},
        {'label': '1Y', 'value': '1y', 'interval': '1d'},
        {'label': '5Y', 'value': '5y', 'interval': '1wk'},
        {'label': 'MAX', 'value': 'max', 'interval': '1mo'},
    ]
    
    return render(request, 'charts/stock_price.html', {
        'company': company,
        'ranges': ranges,
        'default_range': 'ytd'
    })

def price_data_json(request, ticker):
    """Return JSON data for stock price chart."""
    ticker = ticker.upper()
    
    # Get time range parameters
    period = request.GET.get('period', 'ytd')
    interval = request.GET.get('interval', '1d')
    
    try:
        # Fetch data using yfinance
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period=period, interval=interval)
        
        # Format data for chart
        data = []
        for date, row in hist.iterrows():
            # Convert date to timestamp for Chart.js
            timestamp = int(date.timestamp() * 1000)
            
            data.append({
                'date': timestamp,
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })
        
        return JsonResponse({
            'ticker': ticker,
            'data': data,
            'period': period,
            'interval': interval
        })
        
    except Exception as e:
        logger.error(f"Error fetching price data for {ticker}: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def financial_chart(request, ticker):
    """Render a page with financial metric charts."""
    ticker = ticker.upper()
    company = get_company_data(ticker)
    
    if not company:
        return JsonResponse({'error': 'Company not found'}, status=404)
    
    # Available metrics for dropdown
    metrics = [
        {'label': 'Revenue', 'value': 'revenue'},
        {'label': 'Net Income', 'value': 'net_income'},
        {'label': 'EBITDA', 'value': 'ebitda'},
        {'label': 'EPS', 'value': 'eps'},
        {'label': 'Free Cash Flow', 'value': 'fcf'},
        {'label': 'Profit Margin', 'value': 'profit_margin'},
        {'label': 'Operating Margin', 'value': 'operating_margin'},
        {'label': 'ROE', 'value': 'roe'},
        {'label': 'ROA', 'value': 'roa'},
    ]
    
    return render(request, 'charts/financial_chart.html', {
        'company': company,
        'metrics': metrics,
        'default_metric': 'revenue'
    })

def financial_data_json(request, ticker):
    """Return JSON data for financial metric charts."""
    ticker = ticker.upper()
    metric = request.GET.get('metric', 'revenue')
    period = request.GET.get('period', 'annual')
    
    try:
        ticker_obj = yf.Ticker(ticker)
        
        # Get appropriate financial statements based on metric
        if period == 'annual':
            income_stmt = ticker_obj.income_stmt
            balance_sheet = ticker_obj.balance_sheet
            cash_flow = ticker_obj.cashflow
        else:  # quarterly
            income_stmt = ticker_obj.quarterly_income_stmt
            balance_sheet = ticker_obj.quarterly_balance_sheet
            cash_flow = ticker_obj.quarterly_cashflow
        
        # Map metric to dataframe and field
        metric_mapping = {
            'revenue': (income_stmt, 'Total Revenue'),
            'net_income': (income_stmt, 'Net Income'),
            'ebitda': (income_stmt, 'EBITDA'),
            'eps': (income_stmt, 'Basic EPS'),
            'fcf': (cash_flow, 'Free Cash Flow'),
            'profit_margin': (None, None),  # Calculate custom
            'operating_margin': (None, None),  # Calculate custom
            'roe': (None, None),  # Calculate custom
            'roa': (None, None),  # Calculate custom
        }
        
        # Prepare result data
        result = {
            'ticker': ticker,
            'metric': metric,
            'period': period,
            'data': []
        }
        
        if metric in ('profit_margin', 'operating_margin', 'roe', 'roa'):
            # Calculate custom metrics
            if metric == 'profit_margin':
                revenue = income_stmt.loc['Total Revenue'] if 'Total Revenue' in income_stmt.index else None
                net_income = income_stmt.loc['Net Income'] if 'Net Income' in income_stmt.index else None
                
                if revenue is not None and net_income is not None:
                    for col in income_stmt.columns:
                        if revenue[col] > 0:
                            value = (net_income[col] / revenue[col]) * 100
                            result['data'].append({
                                'date': col.strftime('%Y-%m-%d'),
                                'value': float(value)
                            })
            
            elif metric == 'operating_margin':
                revenue = income_stmt.loc['Total Revenue'] if 'Total Revenue' in income_stmt.index else None
                operating_income = income_stmt.loc['Operating Income'] if 'Operating Income' in income_stmt.index else None
                
                if revenue is not None and operating_income is not None:
                    for col in income_stmt.columns:
                        if revenue[col] > 0:
                            value = (operating_income[col] / revenue[col]) * 100
                            result['data'].append({
                                'date': col.strftime('%Y-%m-%d'),
                                'value': float(value)
                            })
            
            elif metric == 'roe':
                net_income = income_stmt.loc['Net Income'] if 'Net Income' in income_stmt.index else None
                equity = balance_sheet.loc['Total Stockholder Equity'] if 'Total Stockholder Equity' in balance_sheet.index else None
                
                if net_income is not None and equity is not None:
                    for col in income_stmt.columns:
                        if col in equity.index and equity[col] > 0:
                            value = (net_income[col] / equity[col]) * 100
                            result['data'].append({
                                'date': col.strftime('%Y-%m-%d'),
                                'value': float(value)
                            })
            
            elif metric == 'roa':
                net_income = income_stmt.loc['Net Income'] if 'Net Income' in income_stmt.index else None
                assets = balance_sheet.loc['Total Assets'] if 'Total Assets' in balance_sheet.index else None
                
                if net_income is not None and assets is not None:
                    for col in income_stmt.columns:
                        if col in assets.index and assets[col] > 0:
                            value = (net_income[col] / assets[col]) * 100
                            result['data'].append({
                                'date': col.strftime('%Y-%m-%d'),
                                'value': float(value)
                            })
        else:
            # Get standard metric
            df, field = metric_mapping[metric]
            
            if df is not None and field in df.index:
                for col in df.columns:
                    result['data'].append({
                        'date': col.strftime('%Y-%m-%d'),
                        'value': float(df.loc[field, col])
                    })
        
        # Sort by date
        result['data'].sort(key=lambda x: x['date'])
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error fetching financial data for {ticker}: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def comparison_chart(request):
    """Render a page with peer comparison charts."""
    tickers = request.GET.get('tickers', '')
    tickers = [t.strip().upper() for t in tickers.split(',') if t.strip()]
    
    if not tickers:
        # Default to some large tech companies
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'META', 'AMZN']
    
    # Get company data for each ticker
    companies = []
    for ticker in tickers:
        company = get_company_data(ticker)
        if company:
            companies.append(company)
    
    # Available metrics for dropdown
    metrics = [
        {'label': 'Stock Price (YTD)', 'value': 'price_ytd'},
        {'label': 'Market Cap', 'value': 'market_cap'},
        {'label': 'P/E Ratio', 'value': 'pe_ratio'},
        {'label': 'Revenue Growth', 'value': 'revenue_growth'},
        {'label': 'Profit Margin', 'value': 'profit_margin'},
        {'label': 'Dividend Yield', 'value': 'dividend_yield'},
    ]
    
    return render(request, 'charts/comparison_chart.html', {
        'companies': companies,
        'tickers': ','.join(tickers),
        'metrics': metrics,
        'default_metric': 'price_ytd'
    })

def comparison_data_json(request):
    """Return JSON data for company comparison charts."""
    tickers = request.GET.get('tickers', '')
    tickers = [t.strip().upper() for t in tickers.split(',') if t.strip()]
    metric = request.GET.get('metric', 'price_ytd')
    
    if not tickers:
        return JsonResponse({'error': 'No tickers provided'}, status=400)
    
    try:
        # Prepare result container
        result = {
            'metric': metric,
            'data': {}
        }
        
        for ticker in tickers:
            ticker_obj = yf.Ticker(ticker)
            
            if metric == 'price_ytd':
                # Get YTD price performance
                hist = ticker_obj.history(period='ytd')
                if not hist.empty:
                    start_price = hist.iloc[0]['Close']
                    prices = []
                    
                    for date, row in hist.iterrows():
                        price = row['Close']
                        change_pct = ((price - start_price) / start_price) * 100
                        prices.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'value': float(change_pct)
                        })
                    
                    result['data'][ticker] = prices
            
            elif metric == 'market_cap':
                # For metrics that are single values, we'll compare current values
                info = ticker_obj.info
                if 'marketCap' in info:
                    result['data'][ticker] = [{
                        'label': ticker,
                        'value': info['marketCap']
                    }]
            
            elif metric == 'pe_ratio':
                info = ticker_obj.info
                if 'trailingPE' in info:
                    result['data'][ticker] = [{
                        'label': ticker,
                        'value': info['trailingPE']
                    }]
            
            elif metric == 'revenue_growth':
                # Calculate year-over-year revenue growth
                income_stmt = ticker_obj.income_stmt
                if 'Total Revenue' in income_stmt.index and len(income_stmt.columns) >= 2:
                    revenues = income_stmt.loc['Total Revenue']
                    growth_values = []
                    
                    for i in range(len(revenues) - 1):
                        if revenues.iloc[i+1] > 0:  # Avoid division by zero
                            growth = ((revenues.iloc[i] - revenues.iloc[i+1]) / revenues.iloc[i+1]) * 100
                            growth_values.append({
                                'date': revenues.index[i].strftime('%Y-%m-%d'),
                                'value': float(growth)
                            })
                    
                    result['data'][ticker] = growth_values
            
            elif metric == 'profit_margin':
                info = ticker_obj.info
                if 'profitMargins' in info:
                    result['data'][ticker] = [{
                        'label': ticker,
                        'value': info['profitMargins'] * 100  # Convert to percentage
                    }]
            
            elif metric == 'dividend_yield':
                info = ticker_obj.info
                if 'dividendYield' in info:
                    result['data'][ticker] = [{
                        'label': ticker,
                        'value': info['dividendYield'] * 100  # Convert to percentage
                    }]
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error fetching comparison data: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def technical_chart(request, ticker):
    """Render a page with technical analysis chart."""
    ticker = ticker.upper()
    company = get_company_data(ticker)
    
    if not company:
        return JsonResponse({'error': 'Company not found'}, status=404)
    
    # Available indicators for dropdown
    indicators = [
        {'label': 'Simple Moving Average (SMA)', 'value': 'sma'},
        {'label': 'Exponential Moving Average (EMA)', 'value': 'ema'},
        {'label': 'Relative Strength Index (RSI)', 'value': 'rsi'},
        {'label': 'Moving Average Convergence Divergence (MACD)', 'value': 'macd'},
        {'label': 'Bollinger Bands', 'value': 'bollinger'},
    ]
    
    # Time ranges for chart
    ranges = [
        {'label': '1M', 'value': '1mo'},
        {'label': '3M', 'value': '3mo'},
        {'label': '6M', 'value': '6mo'},
        {'label': 'YTD', 'value': 'ytd'},
        {'label': '1Y', 'value': '1y'},
        {'label': '2Y', 'value': '2y'},
    ]
    
    return render(request, 'charts/technical_chart.html', {
        'company': company,
        'indicators': indicators,
        'ranges': ranges,
        'default_range': '6mo',
        'default_indicator': 'sma'
    })

def technical_data_json(request, ticker):
    """Return JSON data for technical analysis chart."""
    ticker = ticker.upper()
    indicator = request.GET.get('indicator', 'sma')
    period = request.GET.get('period', '6mo')
    
    try:
        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(period=period)
        
        # Prepare price data
        price_data = []
        for date, row in hist.iterrows():
            price_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume'])
            })
        
        # Calculate indicator data
        indicator_data = []
        
        if indicator == 'sma':
            # Simple Moving Average with 20, 50, 200 day periods
            sma_periods = [20, 50, 200]
            
            for period in sma_periods:
                if len(hist) >= period:
                    sma = hist['Close'].rolling(window=period).mean()
                    
                    for date, value in sma.items():
                        if not pd.isna(value):
                            indicator_data.append({
                                'type': f'SMA{period}',
                                'date': date.strftime('%Y-%m-%d'),
                                'value': float(value)
                            })
        
        elif indicator == 'ema':
            # Exponential Moving Average with 12, 26 day periods
            ema_periods = [12, 26]
            
            for period in ema_periods:
                if len(hist) >= period:
                    ema = hist['Close'].ewm(span=period, adjust=False).mean()
                    
                    for date, value in ema.items():
                        if not pd.isna(value):
                            indicator_data.append({
                                'type': f'EMA{period}',
                                'date': date.strftime('%Y-%m-%d'),
                                'value': float(value)
                            })
        
        elif indicator == 'rsi':
            # Relative Strength Index (14-day period)
            if len(hist) >= 15:  # Need at least 15 data points for 14-day RSI
                delta = hist['Close'].diff()
                gain = delta.clip(lower=0)
                loss = -delta.clip(upper=0)
                
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
                
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
                
                for date, value in rsi.items():
                    if not pd.isna(value):
                        indicator_data.append({
                            'type': 'RSI',
                            'date': date.strftime('%Y-%m-%d'),
                            'value': float(value)
                        })
        
        elif indicator == 'macd':
            # MACD (12-day EMA - 26-day EMA), with 9-day EMA signal line
            if len(hist) >= 26:
                ema12 = hist['Close'].ewm(span=12, adjust=False).mean()
                ema26 = hist['Close'].ewm(span=26, adjust=False).mean()
                macd_line = ema12 - ema26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                
                for date in macd_line.index:
                    if not pd.isna(macd_line[date]) and not pd.isna(signal_line[date]):
                        indicator_data.append({
                            'type': 'MACD',
                            'date': date.strftime('%Y-%m-%d'),
                            'value': float(macd_line[date]),
                            'signal': float(signal_line[date])
                        })
        
        elif indicator == 'bollinger':
            # Bollinger Bands (20-day SMA with 2 standard deviations)
            if len(hist) >= 20:
                sma20 = hist['Close'].rolling(window=20).mean()
                std20 = hist['Close'].rolling(window=20).std()
                
                upper_band = sma20 + (std20 * 2)
                lower_band = sma20 - (std20 * 2)
                
                for date in sma20.index:
                    if not pd.isna(sma20[date]) and not pd.isna(upper_band[date]) and not pd.isna(lower_band[date]):
                        indicator_data.append({
                            'type': 'Bollinger',
                            'date': date.strftime('%Y-%m-%d'),
                            'middle': float(sma20[date]),
                            'upper': float(upper_band[date]),
                            'lower': float(lower_band[date])
                        })
        
        return JsonResponse({
            'ticker': ticker,
            'indicator': indicator,
            'period': period,
            'price_data': price_data,
            'indicator_data': indicator_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching technical data for {ticker}: {e}")
        return JsonResponse({'error': str(e)}, status=500)