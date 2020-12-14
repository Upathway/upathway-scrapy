from datetime import datetime

import pytz
from neomodel import (config, StructuredNode, StringProperty, IntegerProperty,
                      UniqueIdProperty, RelationshipTo, ArrayProperty, Relationship, StructuredRel, DateTimeProperty)

from neomodel import config

from UniScrapy.neo4j.relationship.SubjectRel import SubjectRel

class Subject(StructuredNode):
    uid = UniqueIdProperty()
    code = StringProperty(unique_index=True, required=True)
    name = StringProperty(unique_index=True, required=True)
    prerequisites = Relationship('Subject', 'PREREQUISITES', model=SubjectRel)
    corequisites = Relationship('Subject', 'COREQUISITES', model=SubjectRel)


