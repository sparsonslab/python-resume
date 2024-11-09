
from functools import reduce
from itertools import chain
import fnmatch
import uuid
import datetime

from database import DataBase


class DictionaryDataBase(DataBase):
    """

    Attributes
    ----------
    fields: {(str, str): Callable}
    """
    def __init__(self, fields):
        super().__init__()
        self.fields = {
            (full.lower(), abbr.lower(), typ): foo
            for (full, abbr, typ), foo in fields.items()
        }
        self.data = {}
        self.indexes = {}
        self.universal_set = set()

    def set_data(self, data):
        if data is not None:
            self.data = {uuid.uuid4(): entry for entry in data}

        self.indexes = {}
        for k, foo in self.fields.items():
            self.indexes[k] = {}
            for idx, entry in self.data.items():
                try:
                    x = foo(entry)
                    if isinstance(x, k[2]):  # type check
                        self.indexes[k][idx] = x
                except KeyError:
                    pass

        self.universal_set = set(self.data.keys())

    def _match_field(self, field):
        f = field.lower()
        for k in self.fields.keys():
            if f == k[0] or f == k[1]:
                return k
        raise ValueError(f"Field {field} not recognised.")

    def search_not(self, operands):
        return self.universal_set - operands.evaluate()

    def search_and(self, operands):
        return reduce(lambda x, y: x & y, [oper.evaluate() for oper in operands])

    def search_or(self, operands):
        return reduce(lambda x, y: x | y, [oper.evaluate() for oper in operands])

    def search_string(self, term, field):
        # Field and type check.
        k = self._match_field(field)

        # String
        if k[2] == str:
            # Wrap search term in wildcards.
            qterm = str(term)
            if qterm[0] != '*':
                qterm = '*' + qterm
            if qterm[-1] != '*':
                qterm += '*'

            # Get matching entries.
            return set([
                idx for idx, entry in self.indexes[k].items()
                if fnmatch.fnmatch(entry, qterm)
            ])

        # Boolean
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
            return(set([idx for idx, entry in self.indexes[k].items() if entry >= qterm]))
        if comp == "<":
            return(set([idx for idx, entry in self.indexes[k].items() if entry <= qterm]))

        raise ValueError(f"Field {field}: {comp} is not a valid comparator.")

    def search_list(self, comp, term, field):
        return set()

    def query(self, query):
        return [self.data[idx] for idx in super().query(query)]
