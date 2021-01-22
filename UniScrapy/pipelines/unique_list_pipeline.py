import json
import logging
import treq
from neomodel import config, clear_neo4j_database, db
from scrapy.exceptions import DropItem
from twisted.internet import defer

from UniScrapy.neo4j.model.subject import Subject

class UniqueListPipeline(object):

    def __init__(self):
        pass

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self, spider):
        return

    def close_spider(self, spider):
        return

    def process_item(self, item, spider):
        item = dict(item)
        self.remove_duplicate(item)
        return item

    def remove_duplicate(self, item):
        item["availability"] = list(dict.fromkeys(item["availability"]))
        item["intended_learning_outcome"] = list(dict.fromkeys(item["intended_learning_outcome"]))
        item["generic_skills"] = list(dict.fromkeys(item["generic_skills"]))
        return item