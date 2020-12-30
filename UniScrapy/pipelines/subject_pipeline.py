import logging
from datetime import datetime

import pymongo
import pytz
from neomodel import config
from scrapy.exceptions import DropItem
from scrapy.exporters import CsvItemExporter

from UniScrapy.models.Subject import SubjectModel
from UniScrapy.neo4j.model.subject import Subject


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
        if not SubjectModel.exists():
            SubjectModel.create_table(read_capacity_units=1, write_capacity_units=20, wait=True)

    def close_spider(self, spider):
        return

    def remove_duplication(self, item, spider):
        item["availability"] = list(dict.fromkeys(item["availability"]))
        item["intended_learning_outcome"] = list(dict.fromkeys(item["intended_learning_outcome"]))
        item["generic_skills"] = list(dict.fromkeys(item["generic_skills"]))
        return item

    def convert_credit_to_float(self, item, spider):
        if item["credit"]:
            item["credit"] = float(item["credit"])
        return item

    def process_item(self, item, spider):
        item = dict(item)
        item = self.remove_duplication(item, spider)
        item = self.convert_credit_to_float(item, spider)

        # pop prerequisites from dict as we model prerequisites as relationship in neo4j
        prerequisites = item.pop('prerequisites', None)

        subject_node = Subject.nodes.get_or_none(code=item["code"])
        # attach tags then create a new node
        if not subject_node:
            item = self.attach_tags(item, spider)
            subject_node = Subject(**item).save()

        # TODO: Use try/except block to handle exceptions
        # TODO: Export a list of subject that encounters exception
        subject = SubjectModel(
            code=item["code"],
            name=item["name"],
            handbook_url=item["handbook_url"],
            overview=item["overview"],
            type=item["type"],
            credit=item["credit"],
            availability=item["availability"],
            intended_learning_outcome=item["intended_learning_outcome"],
            generic_skills=item["generic_skills"],
            assessments=item["assessments"],
            date_and_time=item["date_and_time"]
        )
        subject.save()

        # TODO: use batch operation instead of for loop
        for pre in prerequisites:
            # find matching node by subject code and name
            pre_node = Subject.nodes.get_or_none(code=pre["code"])
            # if None is present, create a new node as a placeholder
            if not pre_node:
                pre = self.attach_tags(pre, spider)
                pre_node = Subject(**pre).save()
            # connect nodes as prerequisites
            subject_node.prerequisites.connect(pre_node)

        return item

    def attach_tags(self, item, spider):
        item = dict(item)
        item["level"] = int(item["code"][4])
        item["area_of_study"] = item["code"][0:4]
        return item

class DuplicatesPipeline(object):

    def __init__(self):
        self.ids_seen = set()

    def process_item(self, item, spider):
        if item['code'] in self.ids_seen:
            raise DropItem("Duplicate item found: %s" % item)
        else:
            self.ids_seen.add(item['code'])
            return item