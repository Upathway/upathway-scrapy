import scrapy


class SubjectsSpider(scrapy.Spider):
    name = "subjects"
    start_urls = [
        'https://handbook.unimelb.edu.au/2020/subjects/comp30022',
        'https://handbook.unimelb.edu.au/2020/subjects/comp30026',
        'https://handbook.unimelb.edu.au/2020/subjects/swen30006',
        'https://handbook.unimelb.edu.au/2020/subjects/comp30023'
    ]

    def parse(self, response):

        name = response.css('title::text').get().split(' ')
        yield {
            # Extract the subject information
            'subject': ' '.join(name[0:-7]),
            'code': name[-7][1:-1],
            'overview': response.css('div.course__overview-wrapper p::text').getall()[0],
            'availability': response.css('div.course__overview-box table tr td div::text').getall()
        }

        # Get the 'eligibility and requirements page'
        next_page = response.css('div.layout-sidebar__side__inner ul li a::attr(href)').getall()[1]
        
        if next_page is not None:
            # Pass the requirement page to parseReq function
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parseReq)


    def parseReq(self, response):

        # Get all prerequisites 
        pages = response.css('#prerequisites table.zebra > tr > td a::attr(href)').getall()

        for next_page in pages:
            if next_page is not None:
                next_page = response.urljoin(next_page)
                yield scrapy.Request(next_page, callback=self.parse)