# Scrapy Spider (wuzzufSpider/wuzzufSpider/spiders/wuzzuf.py)
import scrapy
import re
import logging

class WuzzufSpider(scrapy.Spider):
    name = "wuzzuf"
    allowed_domains = ["wuzzuf.net"]

    def __init__(self, search_query="java", requiredPages=1, **kwargs):
        super().__init__(**kwargs)
        self.search_query = search_query
        self.requiredPages = int(requiredPages)
        self.index = 0

    def start_requests(self):
        logging.info(f"Starting scrape with query: {self.search_query} for {self.requiredPages} pages.")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        url = f"https://wuzzuf.net/search/jobs?a=spbg&q={self.search_query}&start={self.index}"
        self.logger.info(f"Starting crawl with URL: {url}")
        yield scrapy.Request(url, callback=self.parse, headers=headers)

    def parse(self, response):
        self.logger.info(f"Scraping page: {self.index} - {response.url}")

        jobs = response.css('div.css-pkv5jc')
        if not jobs:
            self.logger.warning("No jobs found on this page.")
        else:
            self.logger.info(f"Found {len(jobs)} jobs on this page.")

        for job in jobs:
            job_title = job.css('h2.css-m604qf a::text').get(default='N/A')
            company_name = job.css('a.css-17s97q8::text').get(default='N/A')
            location = job.css('span.css-5wys0k::text').get(default='N/A')
            job_url = job.css('h2.css-m604qf a::attr(href)').get()

            self.logger.info(f"Job title: {job_title}, Company: {company_name}, Location: {location}")

            job_types = job.css('div.css-1lh32fc span.css-1ve4b75.eoyjyou0::text').getall()
            job_details_div = job.css('div.css-y4udm8')
            postedDate = job.css('div.css-do6t5g::text').get(default='N/A')
            raw_categories = job_details_div.css('a.css-5x9pm1::text').getall()
            cleaned_categories = [
                re.findall(r'\b([A-Za-z0-9&]+(?: [A-Za-z0-9&]+)*)\b', category.strip())
                for category in raw_categories if category.strip()
            ]
            cleaned_categories = [item for sublist in cleaned_categories for item in sublist if item.strip()]

            description = {
                'level': job_details_div.css('a.css-o171kl::text').get(default='N/A'),
                'experience': job_details_div.css('span::text').re_first(r'(\d+\s*-\s*\d+)\s*Yrs?') or "Not specified",
                'categories': cleaned_categories
            }

            image_url = job.css('img.css-17095x3::attr(src)').get()
            if image_url:
                image_url = response.urljoin(image_url)

            yield {
                'job_title': job_title,
                'company_name': company_name,
                'location': location,
                'datePosted': postedDate,
                'job_url': response.urljoin(job_url) if job_url else 'N/A',
                'job_type': job_types,
                'Description': description,
                'image_url': image_url or 'N/A'
            }

        if self.index + 1 < self.requiredPages:
            self.index += 1
            next_page_url = f"https://wuzzuf.net/search/jobs?a=spbg&q={self.search_query}&start={self.index}"
            self.logger.info(f"Next page URL: {next_page_url}")
            yield response.follow(next_page_url, callback=self.parse)