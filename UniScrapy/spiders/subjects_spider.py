import os
import scrapy
from scrapy.http import Response
import logging
import re
from UniScrapy.items.subject_item import Subject
logger = logging.getLogger(__name__)


class SubjectsSpider(scrapy.Spider):
    name = "subjects"
    custom_settings = {
        "NEO4J_CONNECTION_STRING": os.environ.get('NEO4J_CONNECTION_STRING'),
        "SERVER_ENDPOINT": os.environ.get('SERVER_ENDPOINT'),
        "ITEM_PIPELINES": {
            'UniScrapy.pipelines.subject_pipeline.DuplicatesPipeline': 100,
            'UniScrapy.pipelines.unique_list_pipeline.UniqueListPipeline': 200,
            'UniScrapy.pipelines.subject_pipeline.SubjectPipeline': 300,
            'UniScrapy.pipelines.neo4j_pipeline.Neo4jPipeline': 300,
        }
    }

    start_urls = [
        "https://handbook.unimelb.edu.au/search?types%5B%5D=subject&year=2021&subject_level_type%5B%5D=all&study_periods%5B%5D=all&area_of_study%5B%5D=all&org_unit%5B%5D=all&campus_and_attendance_mode%5B%5D=all&page=1&sort=external_code%7Casc"
    ]
    page_count = 0
    subject_count = 0

    def parse(self, response):

        # Get all subjects' relative links
        subjects_list = response.css("div#search-results ul.search-results__list a::attr(href)").getall()

        # join the links and then parse each subjects
        for subject in subjects_list:
            self.subject_count += 1
            yield response.follow(subject, callback=self.parseSubjectHome)
        
        next_page = response.urljoin(response.css("div#search-results div.search-context span.next a::attr(href)").get())
        self.page_count += 1

        if next_page:
            yield response.follow(next_page, callback=self.parse)


    def parseSubjectHome(self, response: Response):
        
        sspost = Subject()
        # Extract the subject information

        sspost['name'] = response.css("meta[name=short_title]::attr(content)").get()
        sspost['code'] = response.css("meta[name=code]::attr(content)").get()
        points = response.css("meta[name=points]::attr(content)").get()
        if (points):
            sspost['points'] = float(points)


        sspost['type'] = response.css("meta[name=type]::attr(content)").get()
        year = response.css("meta[name=year]::attr(content)").get()
        if (year):
            sspost['year'] = int(year)

        sspost['level'] = int(sspost['code'][4])
        sspost['eligibility_and_requirements_url'] = response.css("meta[name=eligibility_and_requirements]::attr(content)").get()
        sspost['assessment_url'] = response.css("meta[name=assessment]::attr(content)").get()
        sspost['dates_and_times_url'] = response.css("meta[name=dates_and_times]::attr(content)").get()
        sspost['further_information_url'] = response.css("meta[name=further_information]::attr(content)").get()
        sspost['handbook_url'] = response.url

        # The old way of getting code and name from page titel
        # name = response.css('title::text').get().split(' ')
        # sspost['name'] = ' '.join(name[0:-7])
        # sspost['code'] = name[-7][1:-1]

        # The old way of getting type
        # details = response.css('p.header--course-and-subject__details span::text').getall()
        # sspost["type"] = details[0]

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
            if text:
                if strong:
                    text = strong + text
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
            related_dic = dict()
            relate = subject.css('td::text').get()
            names = subject.css('td a::text').get()
            if relate and names:
                code = relate
                name = names
                related_dic['name'] = name
                related_dic['code'] = code
                prerequisites.append(related_dic)
                yield response.follow("https://handbook.unimelb.edu.au/2021/subjects/"+code, callback=self.parseSubjectHome)


        sspost['prerequisites'] = prerequisites
        ass_page = response.css('div.layout-sidebar__side__inner ul li a::attr(href)').getall()[2]

        yield response.follow(ass_page, self.parseSubjectAss, cb_kwargs=dict(sspost=sspost))
    


    def parseSubjectAss(self, response, sspost):
        sspost['assessments'] = []

        for ass in response.css('div.assessment-table table tbody tr'):
            ass_item =dict()
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
            date = dict()
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