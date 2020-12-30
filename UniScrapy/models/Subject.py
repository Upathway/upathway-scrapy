from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, BooleanAttribute, JSONAttribute, UnicodeSetAttribute


class SubjectModel(Model):
    """
    A DynamoDB Subject
    """
    class Meta:
        table_name = "Subject"
    code = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute()
    type = UnicodeAttribute()
    credit = NumberAttribute()

    like_count = NumberAttribute(default=0)
    hidden = BooleanAttribute(default=False)
    deleted = BooleanAttribute(default=False)
    availability = UnicodeSetAttribute()
    overview = UnicodeAttribute()
    handbook_url = UnicodeAttribute()
    intended_learning_outcome = UnicodeSetAttribute()
    generic_skills = UnicodeSetAttribute()
    assessments = JSONAttribute()
    date_and_time = JSONAttribute()