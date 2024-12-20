#  (C) Copyright 2017-2024 Sean Parsons, Cambridge, UK.
#               All rights reserved.
#  Permission to use, copy, modify, and distribute this software and its
#  documentation for any purpose and without fee is hereby granted, provided
#  that the above copyright notice appear in all copies and that both that
#  copyright notice and this permission notice appear in supporting
#  documentation.
import fnmatch
from functools import reduce
import operator
import re

from resume.query.FieldSpecification import FieldSpecification
from resume.query.query import Query


class ObjectListQuery(Query):
    """ Query of a list of objects.

    Parameters
    ----------
    fields: {(str, str, type): Callable}
        For each field to be searchable:
        (<full field name>, <abbreviated field name>, <field type>):
        <function that retrieves the field's value from an object>

    Attributes
    ----------
    fields: FieldSpecification
        The fields.
    data: {str: object}
        The database to be searched.
        <unique identifier> : object in database.
    indexes: {(str, str, type): {str: any, ...}, ...}
        Covering indexes for each field.
        (<full field name>, <abbreviated field name>, <field type>):
        {<unique identifier>: field value, ...}
    universal_set: set(str)
        The unique identifiers of all the database entries.
    """
    comparator_map = {">": operator.gt, "<": operator.lt, "=": operator.eq}

    def __init__(self, fields):
        super().__init__()
        self.fields = FieldSpecification(fields)
        self.data = {}
        self.indexes = {k: {} for k in self.fields.keys()}
        self.universal_set = set()

    def add_objects(self, objects, identifier_foo=None):
        """ Add to the data to be searched.

        Parameters
        ----------
        objects: [object]
            The objects that make up the database.
        identifier_foo: Callable or None
            A function that returns the unique identifier of an object.
        """
        i = len(self.universal_set)
        for j, obj in enumerate(objects):
            idx = i + j if identifier_foo is None else identifier_foo(obj)
            self.universal_set.add(idx)
            self.data[idx] = obj
            for k, foo in self.fields.items():
                try:
                    value = foo(obj)
                    if isinstance(value, k[2]):  # type check
                        self.indexes[k][idx] = value
                except Exception:
                    pass

    def query(self, query):
        """ Query the objects. """
        return [self.data[idx] for idx in super().query(query)]

    # -------------------------------------------------------------------------
    # Operand evaluation methods.
    # -------------------------------------------------------------------------

    def search_not(self, operand):
        return self.universal_set - operand.evaluate()

    def search_and(self, operands):
        return reduce(lambda x, y: x & y, [oper.evaluate() for oper in operands])

    def search_or(self, operands):
        return reduce(lambda x, y: x | y, [oper.evaluate() for oper in operands])

    def search_string(self, term, field):
        # Field and type check.
        k, op, qterm = self.fields.convert_string(field, term)

        # String field
        if isinstance(qterm, str):
            # Use an re.Pattern object for matching. This is > twice as fast
            # as using fnmatch.fnmatch(entry, qterm).
            qterm_pattern = re.compile(fnmatch.translate(qterm))
            return set([
                idx for idx, entry in self.indexes[k].items()
                if qterm_pattern.search(entry) is not None
            ])

        # Boolean field.
        if isinstance(qterm, bool):
            return set([
                idx for idx, entry in self.indexes[k].items()
                if entry == qterm
            ])

    def search_number(self, comp, term, field):
        k, op, qterm = self.fields.convert_numeric(field, term)

        # Get comparator function.
        comp_foo = self.comparator_map.get(comp, None)
        if comp_foo is None:
            raise ValueError(
                f"Field {field}: {comp} is not a valid comparator.")

        return set([
            idx for idx, entry in self.indexes[k].items()
            if comp_foo(entry, qterm)
        ])

    def search_list(self, comp, term, field):
        k, op, qterm = self.fields.convert_list(field, term)
        return set()
