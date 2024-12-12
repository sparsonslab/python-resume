#  (C) Copyright 2017-2024 Sean Parsons, Cambridge, UK.
#               All rights reserved.
#  Permission to use, copy, modify, and distribute this software and its
#  documentation for any purpose and without fee is hereby granted, provided
#  that the above copyright notice appear in all copies and that both that
#  copyright notice and this permission notice appear in supporting
#  documentation.
import datetime


class FieldSpecification:
    """ A specification for matching and interpreting fields in a
    standardised manner.

    Parameters
    ----------
    fields: {(str, str, type): any}
        For each field to be searchable:
        (<full field name>, <abbreviated field name>, <field type>):
        <some variable or function for returning the field from an entry>

    Attributes
    ----------
    fields: {(str, str, type): any}
        The name as for the parameter, but with the field names (full and
        abbreviated) converted to lower case.
    """
    def __init__(self, fields):
        self.fields = {
            (full.lower(), abbr.lower(), typ): operator
            for (full, abbr, typ), operator in fields.items()
        }

    def items(self):
        for k, v in self.fields.items():
            yield k, v

    def keys(self):
        return self.fields.keys()

    def match(self, field):
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
        for k, v in self.items():
            if f == k[0] or f == k[1]:
                return k, v
        raise ValueError(f"Field {field} not recognised.")

    def convert_string(self, field, term):
        k, v = self.match(field)
        if k[2] == str:
            return k, v, term
        elif k[2] == bool:
            return k, v, term.lower() == "t"
        raise ValueError(f"Field {field} is not string.")

    def convert_numeric(self, field, term):
        k, v = self.match(field)
        if k[2] in [float, int]:
            try:
                return k, v, float(term)
            except ValueError:
                raise ValueError(
                    f"Field {field}: {term} cannot be converted into a number.")

        elif k[2] == datetime.datetime:
            try:
                # todo - allow different datetime formats?
                return k, v, datetime.datetime.strptime(term, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"Field {field}: {term} cannot be converted into a date.")

        raise ValueError(f"Field {field} is not numeric.")

    def convert_list(self, field, term):
        k, v = self.match(field)
        if k[2] == list:
            return k, v, term.split(",")
        raise ValueError(f"Field {field} is not a list.")




