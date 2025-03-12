# stock_data/models.py
import datetime

from django.db import models
from django.utils import timezone


class Company(models.Model):
    """Model to cache company data fetched from yfinance."""
    ticker = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=255)
    sector = models.CharField(max_length=100, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    website = models.URLField(max_length=255, null=True, blank=True)
    logo_url = models.URLField(max_length=255, null=True, blank=True)
    last_updated = models.DateTimeField(default=timezone.now)
    
    def is_stale(self):
        """Check if data needs updating (older than 24 hours)."""
        return timezone.now() - self.last_updated > datetime.timedelta(hours=24)
    
    def __str__(self):
        return f"{self.ticker}: {self.name}"

class FinancialData(models.Model):
    """Model to store financial metrics for companies."""
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='financials')
    # Market data
    market_cap = models.BigIntegerField(null=True, blank=True)
    current_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_change_ytd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Valuation metrics
    pe_ratio = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ps_ratio = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pb_ratio = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ev_ebitda = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    fcf_yield = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    
    # Quality metrics
    quality_score = models.IntegerField(null=True, blank=True)  # Piotroski Score
    profit_margin = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    operating_margin = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    
    # Balance sheet data
    cash = models.BigIntegerField(null=True, blank=True)
    total_debt = models.BigIntegerField(null=True, blank=True)
    net_cash = models.BigIntegerField(null=True, blank=True)
    shares_outstanding = models.BigIntegerField(null=True, blank=True)
    
    # Dividend data
    dividend_yield = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    payout_ratio = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    ex_dividend_date = models.DateField(null=True, blank=True)
    
    last_updated = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Financial Data for {self.company.ticker}"

class SearchResult(models.Model):
    """Model to cache search results for company names."""
    query = models.CharField(max_length=255)
    results_json = models.JSONField()  # Store list of matches as JSON
    last_updated = models.DateTimeField(default=timezone.now)
    
    def is_stale(self):
        """Check if results are stale (older than 1 week)."""
        return timezone.now() - self.last_updated > datetime.timedelta(days=7)
    
    def __str__(self):
        return f"Search for: {self.query}"