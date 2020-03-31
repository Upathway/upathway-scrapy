import scrapy
from UniScrapy.items import UniscrapyItem


class SubjectsSpider(scrapy.Spider):
    name = "subjects"
    start_urls = [
        # All undergraduate CIS subjects
        'https://handbook.unimelb.edu.au/search?area_of_study%5B%5D=all&campus_and_attendance_mode%5B%5D=all&org_unit%5B%5D=4180&sort=_score%7Cdesc&study_periods%5B%5D=all&subject_level_type%5B%5D=undergraduate&types%5B%5D=subject&year=2020'
    ]

    def parse(self, response):

        # Get all subjects' relative links
        subjects_list = response.css("div#search-results ul.search-results__list a::attr(href)").getall()

        # join the links and then parse each subjects
        for subject in subjects_list:
            yield response.follow(subject, callback=self.parseSubject)
        
        next_page = response.urljoin(response.css("div#search-results div.search-context span.next a::attr(href)").get())

        if next_page:
            yield response.follow(next_page, callback=self.parse)

        

    def parseSubject(self, response):

        name = response.css('title::text').get().split(' ')

        sspost = UniscrapyItem()

        # Extract the subject information
        sspost['subject'] = ' '.join(name[0:-7])
        sspost['code'] = name[-7][1:-1]
        sspost['overview'] = response.css('div.course__overview-wrapper p::text').getall()[0]
        sspost['availability'] = response.css('div.course__overview-box table tr td div::text').getall()


        yield sspost

        

        '''
        # Get the 'eligibility and requirements page'
        next_page = response.css('div.layout-sidebar__side__inner ul li a::attr(href)').getall()[1]
        
        if next_page is not None:
            # Pass the requirement page to parseReq function
            next_page = response.urljoin(next_page)
            yield scrapy.Request(next_page, callback=self.parseReq)
        '''