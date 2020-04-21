# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class UniscrapyItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    subject = scrapy.Field()
    code = scrapy.Field()
    overview = scrapy.Field()
    ILO = scrapy.Field()
    generic_skills = scrapy.Field()
    availability = scrapy.Field()
    prerequisites = scrapy.Field()
    assessments = scrapy.Field()
    date_n_time = scrapy.Field()

