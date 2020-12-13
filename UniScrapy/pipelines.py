import logging

import pymongo
from neomodel import config
from scrapy.exceptions import DropItem

from UniScrapy.neo4j.model.Subject import Subject


class UniscrapyPipeline(object):

    collection_name = 'subjects'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        config.DATABASE_URL = 'bolt://neo4j:test@192.168.1.17:7687'  # default

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        item = dict(item)
        # pop prerequisites from dict as we model prerequisites as relationship in neo4j
        prerequisites = item.pop('prerequisites', None)

        subject_node = Subject.nodes.get_or_none(code=item["code"])
        # Update existing subject (usually a placeholder)
        if (subject_node):
            subject_node.name = item["name"]
            subject_node.overview = item["overview"]
            subject_node.intended_learning_outcome = item["intended_learning_outcome"]
            subject_node.generic_skills = item["generic_skills"]
            subject_node.availability = item["availability"]
            subject_node.assessments = item["assessments"]
            subject_node.date_and_time = item["date_and_time"]
        else:
            subject_node = Subject(**item).save()

        for pre in prerequisites:
            # find matching node by subject code and name
            pre_node = Subject.nodes.get_or_none(code=pre["code"])
            # if None is present, create a new node as a placeholder
            if not pre_node:
                pre_node = Subject(**pre).save()
            # connect nodes as prerequisites
            subject_node.prerequisites.connect(pre_node)
        return item


class DuplicatesPipeline(object):

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['name'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(item['name'])
            return item
