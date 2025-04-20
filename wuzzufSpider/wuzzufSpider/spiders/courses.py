import scrapy

class ClassCentralSpider(scrapy.Spider):
    name = "classcentral_pure"
    allowed_domains = ["classcentral.com"]

    def __init__(self, query="python", pages=1,language='arabic', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.query = query
        self.pages = int(pages)
        self.language = language

    def start_requests(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        for page in range(1, self.pages + 1):
            url = f"https://www.classcentral.com/search?q={self.query}&lang={self.language}&page={page}"
        yield scrapy.Request(url, callback=self.parse, headers=headers)

    def parse(self, response):

        courses = response.css("li.course-list-course")
        for course in courses:
            title = course.css("h2.text-1::text").get(default="").strip()
            description = course.css("p.text-2.margin-bottom-xsmall a::text").get(default="").strip()
            image = course.css("img.absolute.top.left.width-100.height-100.cover.block::attr(src)").get()

            # Extract details
            details = {}
            for item in course.css("ul.margin-top-small li"):
                icon_class = item.css("i::attr(class)").get("")
                text = item.css("span.text-3::text, a.text-3::text").get(default="").strip()

                if "icon-provider" in icon_class:
                    details["provider"] = text
                elif "icon-clock" in icon_class:
                    details["duration"] = text
                elif "icon-calendar" in icon_class:
                    details["start_date"] = text
                elif "icon-dollar" in icon_class:
                    details["pricing"] = text

            yield {
                "title": title,
                "description": description,
                "image": image,
                "details": details
            }
