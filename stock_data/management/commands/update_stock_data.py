# stock_data/management/commands/update_stock_data.py
import logging
import time

from django.core.management.base import BaseCommand
from django.utils import timezone
from stock_data.models import Company, FinancialData
from stock_data.utils import fetch_company_info, fetch_financial_data

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Update stock data for all companies in the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Update all companies regardless of last update time',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of companies to update',
        )

    def handle(self, *args, **options):
        update_all = options['all']
        limit = options.get('limit')
        
        # Get companies that need updating (older than 24 hours)
        one_day_ago = timezone.now() - timezone.timedelta(hours=24)
        
        if update_all:
            companies = Company.objects.all()
        else:
            companies = Company.objects.filter(last_updated__lt=one_day_ago)
        
        if limit:
            companies = companies[:limit]
        
        total_companies = companies.count()
        self.stdout.write(f"Updating data for {total_companies} companies...")
        
        updated_count = 0
        error_count = 0
        
        for company in companies:
            self.stdout.write(f"Updating {company.ticker}...", ending='')
            
            try:
                # Update company info
                company_info = fetch_company_info(company.ticker)
                if company_info:
                    for key, value in company_info.items():
                        if key != 'ticker' and hasattr(company, key):
                            setattr(company, key, value)
                    company.last_updated = timezone.now()
                    company.save()
                
                # Update financial data
                financial_data = fetch_financial_data(company.ticker)
                if financial_data:
                    financials, created = FinancialData.objects.get_or_create(company=company)
                    
                    for key, value in financial_data.items():
                        if hasattr(financials, key):
                            setattr(financials, key, value)
                    
                    financials.last_updated = timezone.now()
                    financials.save()
                
                self.stdout.write(self.style.SUCCESS(" Done"))
                updated_count += 1
                
                # Sleep to avoid hitting API limits
                time.sleep(1)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f" Error: {str(e)}"))
                logger.error(f"Error updating {company.ticker}: {e}")
                error_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"Updated {updated_count} companies successfully. {error_count} errors."
        ))