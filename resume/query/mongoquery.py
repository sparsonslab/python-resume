#  (C) Copyright 2017-2024 Sean Parsons, Cambridge, UK.
#               All rights reserved.
#  Permission to use, copy, modify, and distribute this software and its
#  documentation for any purpose and without fee is hereby granted, provided
#  that the above copyright notice appear in all copies and that both that
#  copyright notice and this permission notice appear in supporting
#  documentation.
import datetime

from resume.query.query import Query, convert_term_to_type


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
    fields: {(str, str, type): str}
        The name as for the parameter, but with the field names (full and
        abbreviated) converted to lower case.
    """
    comparator_map = {">": "$gt", "<": "$lt", "=": "$eq"}

    def __init__(self, fields):
        super().__init__()
        self.fields = {
            (full.lower(), abbr.lower(), typ): path
            for (full, abbr, typ), path in fields.items()
        }

    def _match_field(self, field):
        f = field.lower()
        for k, v in self.fields.items():
            if f == k[0] or f == k[1]:
                return k, v
        raise ValueError(f"Field {field} not recognised.")

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
        # Field and type check.
        k, v = self._match_field(field)

        #  Convert search term to a string or bool
        qterm = convert_term_to_type(
            field, term,
            target_type=k[2],
            possible_types=(str, bool)
        )

        # String field
        if isinstance(qterm, str):
            if "*" in qterm:
                return {v: {"$regex": qterm.replace("*", "")}}
            return {v: qterm}

        # Boolean field.
        if isinstance(qterm, bool):
            return {v: qterm}

    def search_number(self, comp, term, field):
        # Field and type check.
        k, v = self._match_field(field)

        # Convert search term to a number or datetime.
        qterm = convert_term_to_type(
            field, term,
            target_type=k[2],
            possible_types=(float, int, datetime.datetime)
        )

        # Get comparator operator.
        comp_op = self.comparator_map.get(comp, None)
        if comp_op is None:
            raise ValueError(
                f"Field {field}: {comp} is not a valid comparator.")
        return {v: {comp_op: qterm}}

    def search_list(self, comp, term, field):
        # Field and type check.
        k, v = self._match_field(field)

        # Convert search term to a list.
        qterm = convert_term_to_type(
            field, term,
            target_type=k[2],
            possible_types=[list]
        )

        return {v: {"$in": qterm}}
