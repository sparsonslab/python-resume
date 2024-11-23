#  (C) Copyright 2017-2024 Sean Parsons, Cambridge, UK.
#               All rights reserved.
#  Permission to use, copy, modify, and distribute this software and its
#  documentation for any purpose and without fee is hereby granted, provided
#  that the above copyright notice appear in all copies and that both that
#  copyright notice and this permission notice appear in supporting
#  documentation.

from resume.query.query import Query


class SQLQuery(Query):

    def __init__(self, field_names):
        super().__init__()
        self.field_names = {k.lower(): v.lower() for k, v in field_names.items()}

    def _get_field_full_name(self, field_name):
        m = field_name.lower()
        for abbr, full in self.field_names.items():
            if m == abbr or m == full:
                return full
        return m

    # -------------------------------------------------------------------------
    # Database specific search actions.
    # -------------------------------------------------------------------------

    def search_not(self, operands):
        return 'NOT ' + operands.evaluate()

    def search_and(self, operands):
        return "(" + " AND ".join([oper.evaluate() for oper in operands]) + ")"

    def search_or(self, operands):
        return "(" + " OR ".join([oper.evaluate() for oper in operands]) + ")"

    def search_string(self, term, field):
        nom = self._get_field_full_name(field)
        x = term.replace("*", "%")
        return f"\"{nom}\" LIKE '{x}'"

    def search_number(self, comp, term, field):
        nom = self._get_field_full_name(field)
        return f"\"{nom}\" {comp} {term}"

    def search_list(self, comp, term, field):
        return ""
