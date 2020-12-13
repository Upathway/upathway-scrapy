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
    overview = StringProperty()
    intended_learning_outcome = ArrayProperty()
    generic_skills = ArrayProperty()
    availability = ArrayProperty()
    assessments = ArrayProperty()
    date_and_time = ArrayProperty()
    last_update = DateTimeProperty(default=lambda: datetime.now(pytz.utc))
    prerequisites = Relationship('Subject', 'PREREQUISITES', model=SubjectRel)
    corequisites = Relationship('Subject', 'COREQUISITES', model=SubjectRel)


