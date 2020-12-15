import os

import scrapy
import logging

from scrapy.http import Response

from UniScrapy.items import subject_item


class SubjectsSpider(scrapy.Spider):
    name = "subjects"
    custom_settings = {
        "MONGO_URI": os.environ.get('MONGO_URI'),
        "MONGO_DATABASE": os.environ.get('MONGO_DATABASE'),
        "NEO4J_CONNECTION_STRING": os.environ.get('NEO4J_CONNECTION_STRING'),
        "ITEM_PIPELINES": {
            'UniScrapy.pipelines.subject_pipeline.DuplicatesPipeline': 100,
            'UniScrapy.pipelines.subject_pipeline.SubjectPipeline': 300,
        }
    }

    start_urls = [
        # All subjects
        "https://handbook.unimelb.edu.au/search?types%5B%5D=subject&year=2021&level_type%5B%5D=all&campus_and_attendance_mode%5B%5D=all&org_unit%5B%5D=all&page=1&sort=_score%7Cdesc"
        #  All 2021 CIS and Maths subjects
        # "https://handbook.unimelb.edu.au/search?types%5B%5D=subject&year=2021&subject_level_type%5B%5D=all&study_periods%5B%5D=all&area_of_study%5B%5D=all&org_unit%5B%5D=4180&org_unit%5B%5D=6200&campus_and_attendance_mode%5B%5D=all&page=1&sort=_score%7Cdesc"
        # 'https://handbook.unimelb.edu.au/search?types%5B%5D=subject&year=2020&subject_level_type%5B%5D=all&study_periods%5B%5D=all&area_of_study%5B%5D=all&org_unit%5B%5D=4180&org_unit%5B%5D=6200&campus_and_attendance_mode%5B%5D=all&page=1&sort=_score%7Cdesc'
    ]

    def parse(self, response):

        # Get all subjects' relative links
        subjects_list = response.css("div#search-results ul.search-results__list a::attr(href)").getall()

        # join the links and then parse each subjects
        for subject in subjects_list:
            yield response.follow(subject, callback=self.parseSubjectHome)
        
        next_page = response.urljoin(response.css("div#search-results div.search-context span.next a::attr(href)").get())

        if next_page:
            yield response.follow(next_page, callback=self.parse)


    def parseSubjectHome(self, response: Response):
        
        sspost = subject_item()
        # Extract the subject information
        name = response.css('title::text').get().split(' ')
        sspost['handbook_url'] = response.url
        sspost['name'] = ' '.join(name[0:-7])
        sspost['code'] = name[-7][1:-1]
        sspost['overview'] = response.css('div.course__overview-wrapper p::text').getall()[0]

        ILO = response.css('div#learning-outcomes ul li::text').getall()
        if not ILO:
            ILO = response.css('div#learning-outcomes ol li::text').getall()
        sspost['intended_learning_outcome'] = ILO

        
        GS = response.css('div#generic-skills ul li::text').getall()
        if not GS:
            GS = response.css('div#generic-skills ol li::text').getall()
        sspost["generic_skills"] = GS

        sspost['availability'] = response.css('div.course__overview-box table tr td div::text').getall()

        # Get the 'eligibility and requirements page'
        req_page = response.css('div.layout-sidebar__side__inner ul li a::attr(href)').getall()[1]

        yield response.follow(req_page, self.parseSubjectReq, cb_kwargs=dict(sspost=sspost))

    def parseSubjectReq(self, response, sspost):

        prerequisites = []

        for subject in response.css('div#prerequisites table tr'):
            related_dic = {}
            relate = subject.css('td::text').getall()
            names = subject.css('td a::text').getall()
            if relate and names:
                code = relate[0]
                name = names[0]
                related_dic['name'] = name
                related_dic['code'] = code
                prerequisites.append(related_dic)

        sspost['prerequisites'] = prerequisites

        ass_page = response.css('div.layout-sidebar__side__inner ul li a::attr(href)').getall()[2]

        yield response.follow(ass_page, self.parseSubjectAss, cb_kwargs=dict(sspost=sspost))
    


    def parseSubjectAss(self, response, sspost):

        assessments = {}

        i = 0
        for ass in response.css('div.assessment-table table tr'):
            ass_list = []
            if i > 0:
                ass_list.extend(ass.css('td p::text').getall())
                ass_list.extend(ass.css('td::text').getall())
                assessments["assessment "+str(i)] = ass_list
            i += 1
        
        sspost['assessments'] = assessments

        dnt_page = response.css('div.layout-sidebar__side__inner ul li a::attr(href)').getall()[3]

        yield response.follow(dnt_page, self.parseSubjectDNT, cb_kwargs=dict(sspost=sspost))



    def parseSubjectDNT(self, response, sspost):

        availability = sspost['availability']

        date_and_times = {}

        i = 0
        for dnt in response.css('div.course__body__inner ul.accordion li'):
            curr_info = {} 
            k = dnt.css('table tr th::text').getall()
            v = dnt.css('table tr td::text').getall()
            for j in range(len(k)):
                curr_info[k[j]] = v[j]
            # TODO: Replace Index by label name to avoid IndexError
            date_and_times[availability[i]] = curr_info
            i += 1

        sspost['date_and_time'] = date_and_times

        yield sspost