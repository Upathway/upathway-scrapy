import logging
from datetime import datetime

import pymongo
import pytz
from neomodel import config
from scrapy.exceptions import DropItem

from UniScrapy.neo4j.model.subject import Subject


class AreaOfStudyPipeline(object):

    collection_name = 'area_of_study'

    def __init__(self,  mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri = crawler.settings.get('MONGO_URI'),
            mongo_db = crawler.settings.get('MONGO_DATABASE')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        self.save_item(item)

    def validate_item(self, item):
        pass

    def save_item(self, item):
        item = dict(item)
        self.db[self.collection_name].insert_one(item)
        return item


class DuplicatesPipeline(object):

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['prefix'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(item['prefix'])
            return item