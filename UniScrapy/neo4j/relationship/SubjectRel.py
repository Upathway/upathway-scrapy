from neomodel import StructuredRel, StringProperty


class SubjectRel(StructuredRel):
    note = StringProperty(default="")