import logging
from datetime import datetime

import pymongo
import pytz
from neomodel import config
from scrapy.exceptions import DropItem

from UniScrapy.neo4j.model.Subject import Subject


class UniscrapyPipeline(object):

    collection_name = 'subjects'

    def __init__(self,  mongo_uri, mongo_db, neo4j_connection_string):
        self.neo4j_connection_string = neo4j_connection_string
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            neo4j_connection_string=crawler.settings.get('NEO4J_CONNECTION_STRING'),
            mongo_uri = crawler.settings.get('MONGO_URI'),
            mongo_db = crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]
        config.DATABASE_URL = self.neo4j_connection_string  # default

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        item = dict(item)
        # pop prerequisites from dict as we model prerequisites as relationship in neo4j
        prerequisites = item.pop('prerequisites', None)
        item["placeholder"] = False

        subject_node = Subject.nodes.get_or_none(code=item["code"])
        # create a new node
        if not subject_node:
            subject_node = Subject(**item).save()

        subject_doc = self.db[self.collection_name].find_one({"code": item["code"]})
        if not subject_doc:
            self.db[self.collection_name].insert_one(item)
        else:
            self.db[self.collection_name].replace_one(subject_doc, item)

        # TODO: use batch operation instead of for loop
        for pre in prerequisites:
            # find matching node by subject code and name
            pre_node = Subject.nodes.get_or_none(code=pre["code"])
            # if None is present, create a new node as a placeholder
            if not pre_node:
                pre_node = Subject(**pre).save()
                pre["placeholder"] = True
                self.db[self.collection_name].insert_one(dict(pre))
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
