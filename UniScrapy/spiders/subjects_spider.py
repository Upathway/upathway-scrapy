import os
import scrapy
from scrapy.http import Response

import re
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from neomodel import db, clear_neo4j_database

from UniScrapy.items.subject_item import Subject


class SubjectsSpider(scrapy.Spider):
    name = "subjects"
    custom_settings = {
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
        
        sspost = Subject()
        # Extract the subject information
        # header = response.css('span.header--course-and-subject__main ::text').getall()[0]
        # result = re.search(r"([A-Za-z0-9 ]+) \(([A-Za-z0-9_]+)\)", header)
        # sspost['name'] = result.group(1).strip()
        # sspost['code'] = result.group(2).strip()

        name = response.css('title::text').get().split(' ')
        sspost['name'] = ' '.join(name[0:-7])
        sspost['code'] = name[-7][1:-1]
        sspost['handbook_url'] = response.url

        details = response.css('p.header--course-and-subject__details span::text').getall()
        credit_match = re.match(r"Points: (\d*\.?\d*)", details[1])
        if credit_match:
            sspost["credit"] = credit_match.group(1)

        sspost["type"] = details[0]

        overview = response.css('div.course__overview-wrapper p::text').get()
        if overview:
            sspost['overview'] = overview
        ILO = response.css('div#learning-outcomes ul li::text').getall()
        if not ILO:
            ILO = response.css('div#learning-outcomes ol li::text').getall()
        sspost['intended_learning_outcome'] = ILO

        skills = []
        for skill in response.css('div#generic-skills ul.ticked-list'):
            strong = skill.css("li strong::text").get()
            text = skill.css("li::text").get()
            if strong:
                text = strong + text
            if text:
                skills.append(text.strip())

        for skill in response.css('div#generic-skills ol'):
            text = skill.css("li::text").get()
            if text:
                skills.append(text.strip())

        sspost["generic_skills"] = skills
        sspost['availability'] = []

        for term in response.css('div.course__overview-box table tr td div::text'):
            # Extract "Semester 1" from "Semester 1 (Extended) - Online"
            # Also see https://stackoverflow.com/questions/42526951/regex-to-match-text-but-not-if-contained-in-brackets
            term_name = term.get()
            if (term_name == "Time-based Research"):
                sspost['availability'].append(term_name)
            else:
                result = re.search(r"(?<!\()\b[A-Za-z0-9 ]*\b(?![\w\s]*[\)])", term_name)
                if (result):
                    # Only save the first matched group
                    sspost['availability'].append(result.group())
        # Get the 'eligibility and requirements page'

        req_page = response.css('div.layout-sidebar__side__inner ul li a::attr(href)').getall()[1]

        yield response.follow(req_page, self.parsePrerequisites, cb_kwargs=dict(sspost=sspost))

    def parsePrerequisites(self, response, sspost):

        prerequisites = []

        for subject in response.css('div#prerequisites table tr'):
            related_dic = {}
            relate = subject.css('td::text').get()
            names = subject.css('td a::text').get()
            if relate and names:
                code = relate
                name = names
                related_dic['name'] = name
                related_dic['code'] = code
                prerequisites.append(related_dic)

        sspost['prerequisites'] = prerequisites

        for link in response.css('div#prerequisites table tr a::attr(href)').getall():
            yield response.follow(link, callback=self.parseSubjectHome)

        ass_page = response.css('div.layout-sidebar__side__inner ul li a::attr(href)').getall()[2]

        yield response.follow(ass_page, self.parseSubjectAss, cb_kwargs=dict(sspost=sspost))
    


    def parseSubjectAss(self, response, sspost):
        sspost['assessments'] = []

        for ass in response.css('div.assessment-table table tbody tr'):
            ass_item = {}
            description = ass.css('td p::text').get()
            # if have description wrapped in p, then it is a regular assessment
            columns = ass.css('td::text').getall()
            if description:
                ass_item["description"] = description.strip()
                ass_item["percentage"] = columns[-1].strip()
            else:
                ass_item["description"] = columns[0].strip()
                ass_item["percentage"] = columns[-1].strip()
            sspost['assessments'].append(ass_item)

        try:
            dnt_page = response.css('div.layout-sidebar__side__inner ul li a::attr(href)').getall()[3]
            yield response.follow(dnt_page, self.parseSubjectDNT, cb_kwargs=dict(sspost=sspost))
        except IndexError:
            yield sspost

    def parseSubjectDNT(self, response, sspost):
        sspost['date_and_time'] = []
        for term in response.css('ul.accordion li'):
            date = {}
            term_name = term.css("div.accordion__title::text").get()
            if term_name:
                date["term"] = term_name
                date["contact_email"] = term.css("div.course__body__inner__contact_details p a ::text").getall()
                # Add each lines in the table into a dictionary
                for line in term.css('div table tbody tr'):
                    name = re.sub('[- ]', '_', line.css("th::text").get().lower())
                    date[name.strip()] = line.css("td::text").get()
                sspost['date_and_time'].append(date)
        yield sspost