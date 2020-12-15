import json
import os

import scrapy
import logging

from scrapy.http import Response

from UniScrapy.items import subject_item
from UniScrapy.items.area_of_study_item import AreaOfStudy


class AreaOfStudySpider(scrapy.Spider):
    name = "area_of_study"
    custom_settings = {
        "MONGO_URI": os.environ.get('MONGO_URI'),
        "MONGO_DATABASE": os.environ.get('MONGO_DATABASE'),
        "ITEM_PIPELINES": {
            'UniScrapy.pipelines.area_of_study_pipeline.DuplicatesPipeline': 100,
            'UniScrapy.pipelines.area_of_study_pipeline.AreaOfStudyPipeline': 300,

        }
    }


    start_urls = [
        # All subjects
        "https://handbook.unimelb.edu.au/search?types%5B%5D=subject&year=2021&subject_level_type%5B%5D=all&study_periods%5B%5D=all&area_of_study%5B%5D=all&org_unit%5B%5D=all&campus_and_attendance_mode%5B%5D=all&page=1&sort=_score%7Cdesc"
    ]

    def parse(self, response):

        # Get all subjects' relative links
        raw = response.selector.xpath('''//*[@id="search-filters"]/div[4]/fieldset''').xpath('@data-view-filter-field').get()
        fields = json.loads(raw)

        for option in fields["fieldData"]["options"][0]["options"]:
            area = AreaOfStudy()
            area["prefix"] = option["value"]
            area["name"] = option["label"]
            yield area



