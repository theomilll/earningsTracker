def popular_companies(request):
    companies = [
        ('AAPL', 'Apple Inc.'),
        ('MSFT', 'Microsoft Corp.'),
        ('GOOGL', 'Alphabet Inc.'),
        ('AMZN', 'Amazon.com Inc.'),
        ('META', 'Meta Platforms Inc.'),
    ]
    
    return {'popular_companies': companies}