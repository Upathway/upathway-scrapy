# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

class Subject(scrapy.Item):
    code = scrapy.Field()
    name = scrapy.Field()
    year = scrapy.Field()
    level = scrapy.Field()
    type = scrapy.Field()
    points = scrapy.Field()
    eligibility_and_requirements_url = scrapy.Field()
    assessment_url = scrapy.Field()
    dates_and_times_url = scrapy.Field()
    further_information_url = scrapy.Field()
    handbook_url = scrapy.Field()
    overview = scrapy.Field()
    intended_learning_outcome = scrapy.Field()
    generic_skills = scrapy.Field()
    availability = scrapy.Field()
    assessments = scrapy.Field()
    date_and_time = scrapy.Field()
    prerequisites = scrapy.Field()
    corequisites = scrapy.Field()
    area_of_study = scrapy.Field()

