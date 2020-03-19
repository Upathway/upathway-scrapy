import scrapy


class SubjectsSpider(scrapy.Spider):
    name = "subjects"
    start_urls = [
        'https://handbook.unimelb.edu.au/2020/subjects/comp30022/eligibility-and-requirements'
    ]

    def parse(self, response):
        name = response.css('title::text').get().split(' ')
        yield {
            # Need to extract the subject name and code
            'subject': ' '.join(name[3:-7]),
            'code': name[-7][1:-1],
            'availability': None
        }

        next_page = response.css('#prerequisites table.zebra > tr > td a::attr(href)').get()
        
        if next_page is not None:
            # Crawling the prerequisites page
            next_page = response.urljoin(str(next_page)+'/eligibility-and-requirements')
            yield scrapy.Request(next_page, callback=self.parse)