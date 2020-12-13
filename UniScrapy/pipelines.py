import logging
from datetime import datetime

import pymongo
import pytz
from neomodel import config
from scrapy.exceptions import DropItem

from UniScrapy.neo4j.model.Subject import Subject


class UniscrapyPipeline(object):

    collection_name = 'subjects'

    def __init__(self, neo4j_connection_string):
        self.neo4j_connection_string = neo4j_connection_string

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            neo4j_connection_string=crawler.settings.get('NEO4J_CONNECTION_STRING')
        )

    def open_spider(self, spider):
        config.DATABASE_URL = self.neo4j_connection_string  # default

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
            subject_node = Subject(**item)
        subject_node.last_update = datetime.now(pytz.utc)
        subject_node.save()

        # TODO: use batch operation instead of for loop
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
