import os

from pynamodb.models import Model
from pynamodb.attributes import UnicodeAttribute, NumberAttribute, BooleanAttribute, JSONAttribute, UnicodeSetAttribute


class SubjectModel(Model):
    """
    A DynamoDB Subject
    """
    class Meta:
        table_name = os.getenv('SUBJECT_TABLE_NAME')
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region = os.getenv('AWS_REGION')

    code = UnicodeAttribute(hash_key=True)
    name = UnicodeAttribute()
    type = UnicodeAttribute()
    handbook_url = UnicodeAttribute()
    overview = UnicodeAttribute(null=True)

    credit = NumberAttribute(null=True)
    like_count = NumberAttribute(default=0)

    hidden = BooleanAttribute(default=False)
    deleted = BooleanAttribute(default=False)

    availability = JSONAttribute()
    intended_learning_outcome = JSONAttribute()
    generic_skills = JSONAttribute()

    assessments = JSONAttribute()
    date_and_time = JSONAttribute()