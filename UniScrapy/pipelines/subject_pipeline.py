import json
import logging
import treq
from scrapy.exceptions import DropItem
from twisted.internet import defer
logger = logging.getLogger(__name__)

class SubjectPipeline(object):

    def __init__(self, server_endpoint):
        self.server_endpoint = server_endpoint

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            server_endpoint=crawler.settings.get('SERVER_ENDPOINT'),
        )

    def open_spider(self, spider):
        return

    def close_spider(self, spider):
        return

    def process_item(self, item, spider):
        item = dict(item)
        code = item["code"]
        self.save_subject(item)
        self.save_subject_term(code, item["date_and_time"])
        self.save_assessment(code, item["assessments"])
        return item

    @defer.inlineCallbacks
    def save_subject_term(self, code, terms):
        data = json.dumps(terms).encode("utf-8")
        headers = {'content-type': 'application/json'}
        logger.info("{} terms(s) saved for {}".format(len(terms), code))
        yield treq.post(url=self.server_endpoint +  "/subjects/{}/terms/".format(code),
                        data=data,
                        headers=headers)
    @defer.inlineCallbacks
    def save_assessment(self, code, assessments):
        data = json.dumps(assessments).encode("utf-8")
        headers = {'content-type': 'application/json'}
        logger.info("{} assessment(s) saved for {}".format(len(assessments), code))

        yield treq.post(url=self.server_endpoint + "/subjects/{}/assessments/".format(code),
                        data=data,
                        headers=headers)


    @defer.inlineCallbacks
    def save_subject(self, item):
        data = json.dumps(item).encode("utf-8")
        headers = {'content-type': 'application/json'}
        logger.info("Subject {} ({}) saved".format(item["name"], item["code"]))
        yield treq.post(url=self.server_endpoint+"/subjects/", data=data, headers=headers)

    def save_to_es(self, item):
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