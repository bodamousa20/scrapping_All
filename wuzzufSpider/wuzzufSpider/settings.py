
BOT_NAME = "wuzzufSpider"

SPIDER_MODULES = ["wuzzufSpider.spiders"]
NEWSPIDER_MODULE = "wuzzufSpider.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False


USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'

# Set settings whose default value is deprecated to a future-proof value
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
# Limit the number of concurrent requests
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1  # Delay between requests to avoid overloading the server
