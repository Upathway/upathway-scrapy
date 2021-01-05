import json
import logging
from datetime import datetime

import pymongo
import pytz
import requests
from neomodel import config
from scrapy.exceptions import DropItem

from UniScrapy.neo4j.model.subject import Subject


class AreaOfStudyPipeline(object):


    def __init__(self):
        pass

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self, spider):
        pass

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        self.save_study_area(item, spider)

    def validate_item(self, item):
        pass

    def save_study_area(self, item, spider):
        item = dict(item)
        headers = {'content-type': 'application/json'}
        response = requests.post(url="https://e7r6quilrh.execute-api.ap-southeast-2.amazonaws.com/dev/api/v1/study-areas/", data=json.dumps(item), headers=headers)
        if response.status_code != 200:
            logging.error(response.json()["message"])


class DuplicatesPipeline(object):

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['prefix'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(item['prefix'])
            return item