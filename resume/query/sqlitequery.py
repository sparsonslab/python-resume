#  (C) Copyright 2017-2024 Sean Parsons, Cambridge, UK.
#               All rights reserved.
#  Permission to use, copy, modify, and distribute this software and its
#  documentation for any purpose and without fee is hereby granted, provided
#  that the above copyright notice appear in all copies and that both that
#  copyright notice and this permission notice appear in supporting
#  documentation.
import datetime

from resume.query.FieldSpecification import FieldSpecification
from resume.query.query import Query


class SQLiteQuery(Query):
    """ A query builder for SQLite.

    Parameters
    ----------
    fields: {(str, str, type): str}
        For each field to be searchable:
        (<full field name>, <abbreviated field name>, <field type>):
        <colum name of the field in the table>
    table: str
        Name of the table to query.

    Attributes
    ----------
    fields: FieldSpecification
        The fields
    """
    def __init__(self, fields, table):
        super().__init__()
        self.table = table
        self.fields = FieldSpecification(fields)

    def query(self, query):
        where_clause = super().query(query)
        return f"SELECT * FROM {self.table} WHERE {where_clause}"

    # -------------------------------------------------------------------------
    # Database specific search actions.
    # -------------------------------------------------------------------------

    def search_not(self, operands):
        return 'NOT (' + operands.evaluate() + ")"

    def search_and(self, operands):
        return "(" + " AND ".join([oper.evaluate() for oper in operands]) + ")"

    def search_or(self, operands):
        return "(" + " OR ".join([oper.evaluate() for oper in operands]) + ")"

    def search_string(self, term, field):
        k, op, qterm = self.fields.convert_string(field, term)

        if isinstance(qterm, str):
            x = qterm.replace("*", "%")
            return f"\"{op}\" LIKE '{x}'"

        if isinstance(qterm, bool):
            return f"\"{op}\" = {int(qterm)}"

    def search_number(self, comp, term, field):
        k, op, qterm = self.fields.convert_numeric(field, term)

        if isinstance(qterm, (float, int)):
            return f"\"{op}\" {comp} {term}"

        if isinstance(qterm, datetime.datetime):
            # Cast both the entry and the search term as UNIX timestamps
            # (seconds since 1970) to avoid format compatibility issues.
            dt = str(int(qterm.timestamp()))
            return f"CAST(strftime('%s', \"{op}\") AS INT) {comp} {dt}"

    def search_list(self, comp, term, field):
        k, op, qterm = self.fields.convert_list(field, term)

        if isinstance(qterm, list):
            x = ",".join(qterm)
            return f"\"{op}\" IN ({x})"
