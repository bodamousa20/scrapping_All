import scrapy

class ClassCentralSpider(scrapy.Spider):
    name = "classcentral_pure"
    allowed_domains = ["classcentral.com"]
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 2,
        'FEED_EXPORT_ENCODING': 'utf-8'
    }

    def __init__(self, query='python', language='english', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query
        self.language = language.lower()  # Normalize to lowercase

    def start_requests(self):
        headers = {
            'Accept-Language': self.language,
            'Referer': f'https://www.classcentral.com/search?q={self.query}'
        }

        # Validate and normalize language
        if self.language not in ['english', 'arabic']:
            self.language = 'english'  # Default to English if invalid language

        # Build the URL
        url = f"https://www.classcentral.com/search?q={self.query}"
        if self.language == 'arabic':
            url += "&lang=arabic"
        else:
            url += "&lang=english"

        yield scrapy.Request(url, callback=self.parse, headers=headers)

    def parse(self, response):
        courses = response.css("li.course-list-course")

        for course in courses:
            yield {
                "title": course.css("h2.text-1::text").get(default="").strip(),
                "description": course.css("p.text-2.margin-bottom-xsmall a::text").get(default="").strip(),
                "image": course.css("img.absolute.top.left.width-100.height-100.cover.block::attr(src)").get(),
                "link": response.urljoin(course.css("a::attr(href)").get(default="")),
                "details": self.extract_course_details(course)
            }

    def extract_course_details(self, course):
        details = {}
        for item in course.css("ul.margin-top-small li"):
            icon_class = item.css("i::attr(class)").get(default="")
            text = item.css("span.text-3::text, a.text-3::text").get(default="").strip()

            if "icon-provider" in icon_class:
                details["provider"] = text
            elif "icon-clock" in icon_class:
                details["duration"] = text
            elif "icon-calendar" in icon_class:
                details["start_date"] = text
            elif "icon-dollar" in icon_class:
                details["pricing"] = text

        return details
