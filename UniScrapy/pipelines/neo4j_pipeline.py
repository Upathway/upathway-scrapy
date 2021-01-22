import json
import logging
import treq
from neomodel import config, clear_neo4j_database, db
from scrapy.exceptions import DropItem
from twisted.internet import defer

from UniScrapy.neo4j.model.subject import Subject
logger = logging.getLogger(__name__)


class Neo4jPipeline(object):

    def __init__(self, neo4j_connection_string):
        self.neo4j_connection_string = neo4j_connection_string

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            neo4j_connection_string=crawler.settings.get('NEO4J_CONNECTION_STRING'),
        )

    def open_spider(self, spider):
        config.DATABASE_URL = self.neo4j_connection_string  # default
        clear_neo4j_database(db)


    def close_spider(self, spider):
        return

    def process_item(self, item, spider):
        item = dict(item)
        self.save_nodes(item)
        return item

    def save_nodes(self, item):
        # pop prerequisites from dict as we model prerequisites as relationship in neo4j
        prerequisites = item.pop('prerequisites', None)
        subject_node = Subject.nodes.get_or_none(code=item["code"])
        # # attach tags then create a new node
        item = self.attach_tags(item)

        if not subject_node:
            subject_node = Subject(**item)

        subject_node.level = item["level"]
        subject_node.area_of_study = item["area_of_study"]
        subject_node.availability = item["availability"]
        subject_node.save()
        logger.info("Node {} added".format(item["code"]))


        # TODO: use batch operation instead of for loop
        for pre in prerequisites:
            # find matching node by subject code and name
            pre_node = Subject.nodes.get_or_none(code=pre["code"])
            # if None is present, create a new node as a placeholder
            if not pre_node:
                pre_node = Subject(**pre).save()
                logger.info("Node {} added".format(pre["code"]))
            # connect nodes as prerequisites
            subject_node.prerequisites.connect(pre_node)

    def attach_tags(self, item):
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