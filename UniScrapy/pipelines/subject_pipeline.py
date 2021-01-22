import json
import logging
from datetime import datetime

import pymongo
import pytz
import treq
from neomodel import config, clear_neo4j_database, db
from scrapy.exceptions import DropItem
from scrapy.exporters import CsvItemExporter
from twisted.internet import defer

from UniScrapy.neo4j.model.subject import Subject

import requests

class SubjectPipeline(object):

    def __init__(self, neo4j_connection_string):
        self.neo4j_connection_string = neo4j_connection_string

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            neo4j_connection_string=crawler.settings.get('NEO4J_CONNECTION_STRING'),
        )

    def open_spider(self, spider):
        config.DATABASE_URL = self.neo4j_connection_string  # default
        # drop existing nodes and relation in neo4j
        clear_neo4j_database(db)


    def close_spider(self, spider):
        return

    def remove_duplication(self, item, spider):
        item["availability"] = list(dict.fromkeys(item["availability"]))
        item["intended_learning_outcome"] = list(dict.fromkeys(item["intended_learning_outcome"]))
        item["generic_skills"] = list(dict.fromkeys(item["generic_skills"]))
        return item

    def convert_credit_to_float(self, item, spider):
        if "credit" in item and item["credit"]:
            item["credit"] = float(item["credit"])
        return item

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        item = dict(item)
        item = self.remove_duplication(item, spider)
        item = self.convert_credit_to_float(item, spider)

        # pop prerequisites from dict as we model prerequisites as relationship in neo4j
        prerequisites = item.pop('prerequisites', None)

        subject_node = Subject.nodes.get_or_none(code=item["code"])
        # # attach tags then create a new node
        item = self.attach_tags(item, spider)

        if not subject_node:
            subject_node = Subject(**item)

        subject_node.level = item["level"]
        subject_node.area_of_study = item["area_of_study"]
        subject_node.availability = item["availability"]
        subject_node.save()

        data = json.dumps(item).encode("utf-8")
        headers = {'content-type': 'application/json'}
        yield treq.post(url="https://e7r6quilrh.execute-api.ap-southeast-2.amazonaws.com/dev/api/v1/subjects/", data=data, headers=headers)
        logging.info("Subject {} ({}) saved".format(item["name"], item["code"]))
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

    def attach_tags(self, item, spider):
        item = dict(item)
        item["level"] = int(item["code"][4])
        item["area_of_study"] = item["code"][0:4]
        return item

    def save_to_es(self, item, spider):
        data = json.dumps(item).encode("utf-8")
        headers = {'content-type': 'application/json'}
        yield treq.put(url="http://localhost/es/subject/subject/", data=data, headers=headers)

class DuplicatesPipeline(object):

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['code'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(item['code'])
            return item