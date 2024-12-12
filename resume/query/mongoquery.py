#  (C) Copyright 2017-2024 Sean Parsons, Cambridge, UK.
#               All rights reserved.
#  Permission to use, copy, modify, and distribute this software and its
#  documentation for any purpose and without fee is hereby granted, provided
#  that the above copyright notice appear in all copies and that both that
#  copyright notice and this permission notice appear in supporting
#  documentation.

from resume.query.FieldSpecification import FieldSpecification
from resume.query.query import Query


class MongoQuery(Query):
    """ A query builder for MongoDB.

    Parameters
    ----------
    fields: {(str, str, type): str}
        For each field to be searchable:
        (<full field name>, <abbreviated field name>, <field type>):
        <period-delimited pathway of the field in the document>

    Attributes
    ----------
    fields: FieldSpecification
        The fields
    """
    comparator_map = {">": "$gt", "<": "$lt", "=": "$eq"}

    def __init__(self, fields):
        super().__init__()
        self.fields = FieldSpecification(fields)

    # -------------------------------------------------------------------------
    # Database specific search actions.
    # -------------------------------------------------------------------------

    def search_not(self, operand):
        return {"$nor": [operand.evaluate()]}

    def search_and(self, operands):
        return {"$and": [oper.evaluate() for oper in operands]}

    def search_or(self, operands):
        return {"$or": [oper.evaluate() for oper in operands]}

    def search_string(self, term, field):
        k, op, qterm = self.fields.convert_string(field, term)
        # String field
        if isinstance(qterm, str):
            if "*" in qterm:
                return {op: {"$regex": qterm.replace("*", "")}}
            return {op: qterm}

        # Boolean field.
        if isinstance(qterm, bool):
            return {op: qterm}

    def search_number(self, comp, term, field):
        k, op, qterm = self.fields.convert_numeric(field, term)

        # Get comparator operator.
        comp_op = self.comparator_map.get(comp, None)
        if comp_op is None:
            raise ValueError(
                f"Field {field}: {comp} is not a valid comparator.")
        return {op: {comp_op: qterm}}

    def search_list(self, comp, term, field):
        k, op, qterm = self.fields.convert_list(field, term)
        return {op: {"$in": qterm}}
