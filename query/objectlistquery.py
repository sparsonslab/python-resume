#  (C) Copyright 2017-2024 Sean Parsons, Cambridge, UK.
#               All rights reserved.
#  Permission to use, copy, modify, and distribute this software and its
#  documentation for any purpose and without fee is hereby granted, provided
#  that the above copyright notice appear in all copies and that both that
#  copyright notice and this permission notice appear in supporting
#  documentation.
import datetime
import fnmatch
from functools import reduce
from itertools import chain
import uuid

from query import Query


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
    fields: {(str, str, type): Callable}
        The name as for the parameter, but with the field names (full and
        abbreviated) converted to lower case.
    data: {str: object}
        The database to be searched.
        <unique identifier> : object in database.
    indexes: {(str, str, type): {str: any, ...}, ...}
        The indexed field values of the database.
        (<full field name>, <abbreviated field name>, <field type>):
        {<unique identifier>: field value, ...}
    universal_set: set(str)
        The unique identifiers of all the database entries.
    """
    def __init__(self, fields):
        super().__init__()
        self.fields = {
            (full.lower(), abbr.lower(), typ): foo
            for (full, abbr, typ), foo in fields.items()
        }
        self.data = {}
        self.indexes = {k: {} for k in self.fields.keys()}
        self.universal_set = set()

    def add_objects(self, objects):
        """ Add to the data to be searched.

        Parameters
        ----------
        objects: [object]
            The objects that make up the database.
        """
        for object in objects:
            # todo - allow the objects to already be indexed or include an index field.
            idx = uuid.uuid4()
            self.universal_set.add(idx)
            self.data[idx] = object
            for k, foo in self.fields.items():
                try:
                    value = foo(object)
                    if isinstance(value, k[2]):  # type check
                        self.indexes[k][idx] = value
                except Exception:
                    pass

    def query(self, query):
        """ Query the objects. """
        return [self.data[idx] for idx in super().query(query)]

    def _match_field(self, field):
        """ Match a field in a search operand to a database field.

        Parameters
        ----------
        field: str
            The field part of a search expression. i.e. <search-term>[<field>].
            Matching is against the full or abbreviated field names in
            self.fields and is case insensitive.

        Returns
        -------
        (str, str, type)
            The matching field key in self.fields.

        Throws
        ------
        ValueError
            If a matching field is not found.
        """
        f = field.lower()
        for k in self.fields.keys():
            if f == k[0] or f == k[1]:
                return k
        raise ValueError(f"Field {field} not recognised.")

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
        """ String search operation.

        Can be used for both string and boolean fields.
        """
        # Field and type check.
        k = self._match_field(field)

        # String field
        if k[2] == str:
            qterm = str(term)
            return set([
                idx for idx, entry in self.indexes[k].items()
                if fnmatch.fnmatch(entry, qterm)
            ])

        # Boolean field.
        if k[2] == bool:
            qterm = term.lower() == "t"
            return set([
                idx for idx, entry in self.indexes[k].items()
                if entry == qterm
            ])

        raise ValueError(f"Field {field} is not a string or bool.")

    def search_number(self, comp, term, field):
        # Field and type check.
        k = self._match_field(field)

        #  Convert search term to a number or datetime
        if k[2] in (float, int):
            try:
                qterm = float(term)
            except ValueError:
                raise ValueError \
                    (f"Field {field}: {term} cannot be converted into a number.")
        elif k[2] == datetime.datetime:
            try:
                qterm = datetime.datetime.strptime(term, "%Y-%m-%d")
            except ValueError:
                raise ValueError \
                    (f"Field {field}: {term} cannot be converted into a date.")
        else:
            raise ValueError \
                (f"Field {field} is not a float or integer or datetime.")

        # Make comparison.
        if comp == "=":
            return(set([idx for idx, entry in self.indexes[k].items() if entry == qterm]))
        if comp == ">":
            return(set([idx for idx, entry in self.indexes[k].items() if entry > qterm]))
        if comp == "<":
            return(set([idx for idx, entry in self.indexes[k].items() if entry < qterm]))

        raise ValueError(f"Field {field}: {comp} is not a valid comparator.")

    def search_list(self, comp, term, field):
        return set()
