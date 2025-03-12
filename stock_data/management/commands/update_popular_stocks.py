# stock_data/management/commands/update_popular_stocks.py
import time

from core.context_processors import popular_companies
from django.core.management.base import BaseCommand
from stock_data.utils import get_company_data


class Command(BaseCommand):
    help = 'Update data for popular companies more frequently'

    def handle(self, *args, **options):
        # Get popular companies list
        popular = popular_companies(None)['popular_companies']
        tickers = [company[0] for company in popular]
        
        self.stdout.write(f"Updating data for {len(tickers)} popular companies...")
        
        updated_count = 0
        error_count = 0
        
        for ticker in tickers:
            self.stdout.write(f"Updating {ticker}...", ending='')
            
            try:
                company = get_company_data(ticker)
                if company:
                    self.stdout.write(self.style.SUCCESS(" Done"))
                    updated_count += 1
                else:
                    self.stdout.write(self.style.ERROR(" Failed"))
                    error_count += 1
                
                # Sleep to avoid hitting API limits
                time.sleep(1)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f" Error: {str(e)}"))
                error_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"Updated {updated_count} popular companies successfully. {error_count} errors."
        ))