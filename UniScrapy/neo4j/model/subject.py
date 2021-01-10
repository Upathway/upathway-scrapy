from datetime import datetime

import pytz
from neomodel import (config, StructuredNode, StringProperty, IntegerProperty,
                      UniqueIdProperty, RelationshipTo, ArrayProperty, Relationship, StructuredRel, DateTimeProperty,
                      FloatProperty)

from neomodel import config

from UniScrapy.neo4j.relationship.SubjectRel import SubjectRel

class Subject(StructuredNode):
    uid = UniqueIdProperty()
    code = StringProperty(unique_index=True, required=True)
    name = StringProperty(unique_index=True, required=True)
    level = IntegerProperty(required=True)
    area_of_study = StringProperty(required=True)
    credit = FloatProperty()
    type = StringProperty()
    availability = ArrayProperty(StringProperty())
    prerequisites = Relationship('Subject', 'PREREQUISITES', model=SubjectRel)
    corequisites = Relationship('Subject', 'COREQUISITES', model=SubjectRel)


