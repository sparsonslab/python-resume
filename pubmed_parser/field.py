""" Field-entry mapping.
"""
from abc import ABC, abstractmethod
import datetime as dt
import fnmatch
import time
from typing import Any


class Field(ABC):
    """ A field in a search query.

    Given a dictionary of
        index:entry
    pairs, where entry can be any type of object (e.g. a JSON dictionary,
    class instance, etc.) and index is a unique identifier for that entry.

    The task is to return a set of entries that have a 'field' (e.g. JSON
    entry, class attribute) whose value matches some criteria.

    Attributes
    ----------
    full_name: str
        The full name of the field. MUST be lower-case.
    abbr_name: str
        The abbreviated name of the field. MUST be upper-case.
        Used
    type: Type
        The field's type (str/int/list/etc)
    entry_mapping: Callable
        A function that returns the field's value from an entry.
    index_mapping: dict
        The index:value mapping for those entries that contain the field.
    universal_set: set
        The set of all indexes.
        Used for NOT comparisons (see PubmedParser)
    """
    def __init__(self, full_name='field', abbr_name='FLD', entry_mapping=None):

        self.full_name = full_name
        self.abbr_name = abbr_name
        self.type = None

        self.entry_mapping = entry_mapping
        if entry_mapping is None:
            self.entry_mapping = (lambda x: x[self.full_name])

        self.index_mapping = {}
        self.universal_set = set()

    def get_value(self, entry: Any):
        """ Get the field's value from an entry.

        Parameters
        ----------
        entry: Any
            An entry.

        Returns
        -------
        Any or None
            The field's value for the entry or None, if the entry does
            not have the field.
        """
        try:
            return self.entry_mapping(entry)
        except (KeyError, AttributeError):
            return None

    def reset_entries(self, entries: dict):
        """ Reset the index map and universal set according to a new set of
        entries.

        Parameters
        ----------
        entries: dict
            A new index:entry map to be searched.
        """
        self.index_mapping = {}
        self.universal_set = []

        for idx, entry in entries.items():
            self.universal_set.append(idx)
            value = self.get_value(entry)
            if value is not None and isinstance(value, self.type) and (value or self.type == bool):
                self.index_mapping[idx] = value

        self.universal_set = set(self.universal_set)

    @abstractmethod
    def get_entry_set(self, value: Any, operator='='):
        """ Retrieve a set of entries satisfying a criterion as defined
        by a value and operator.

        Parameters
        ----------
        value: Any or str
            A value (matching the field's type) or its string-representation.
        operator: str
            An operator that relates how the passed value should be
            compared to the field's value in an entry.

        Returns
        -------
        set
            The set of indices of the entries that satisfy the
            value-operator criterion.
        """
        pass

    @staticmethod
    def match_field(fields: list, field_name: str):
        """ Match a field name against a list of Field instances

        Parameters
        ----------
        fields: [Field]
            A list of Fields.
        field_name: str
            A full or abbreviated field name to match.

        Returns
        -------
        Field or None
            The matched Field instance or None.
        """
        for field in fields:
            if (field.full_name == field_name.lower()) or \
               (field.abbr_name == field_name.upper()):
                return field
        return None

    @staticmethod
    def get_field_entry_set(fields: list, field_name: str,
                            value: Any, operator='='):
        """ Convenience method for matching a field name against a list
        of Field instances and then calling its get_entry_set (above).

        Parameters
        ----------
        fields: [Field]
            A list of Fields.
        field_name: str
            A full or abbreviated field name to match.
        value: Any or str
            A value (matching the field's type) or its string-representation.
        operator: str
            An operator that relates how the passed value should be
            compared to the field's value in an entry.

        Returns
        -------
        set
            The set of indices of the entries that satisfy the value-operator
            criterion for the matched field. An empty set if field_name
            cannot be matched.
        """
        field = Field.match_field(fields, field_name)
        if field is not None:
            return field.get_entry_set(value=value, operator=operator)
        return set()

    @staticmethod
    def check_field_names(fields: list, field_names: list):
        """ Check if any of the named fields do not exist.

        Parameters
        ----------
        fields: [Field]
            A list of Fields.
        field_names: [str]
            A list of full or abbreviated field names to match.
        """
        return [
            name for name in field_names
            if Field.match_field(fields, name) is None
        ]

    @staticmethod
    def get_full_name(fields, name):
        """ Get a possible field full name corresponding to some name. """
        for field in fields:
            if name.lower() == field.abbr_name.lower():
                return field.full_name
        return name


class StringField(Field):
    """ A field with string values.
    """
    def __init__(self, full_name, abbr_name, entry_mapping):
        super().__init__(full_name, abbr_name, entry_mapping)
        self.type = str

    def get_entry_set(self, value: str, operator='='):
        """
        Parameters
        ----------
        value: str
            A pattern to be queried by fnmatch.
            https://docs.python.org/3/library/fnmatch.html
        operator: str
            Without any function in this case.

        Returns
        -------
        set
            The set of indices of entries t
        """
        value = str(value)
        if value[0] != '*':
            value = '*' + value
        if value[-1] != '*':
            value += '*'

        return set([
            idx for idx, entry_value in self.index_mapping.items()
            if fnmatch.fnmatch(entry_value, value)
        ])

class BooleanField(StringField):
    """ A field with boolean values. """
    def __init__(self, full_name, abbr_name, entry_mapping):
        super().__init__(full_name, abbr_name, entry_mapping)
        self.type = bool

    def get_entry_set(self, value: str, operator='='):
        bvalue = ('t' in value) or ('T' in value)
        return set([
            idx for idx, entry_value in self.index_mapping.items()
            if entry_value == bvalue
        ])


class NumericField(Field):
    """ A field with numerical values.
    """
    def __init__(self, full_name, abbr_name, entry_mapping):
        super().__init__(full_name, abbr_name, entry_mapping)
        self.type = (float, int)

    def get_entry_set(self, value, operator='='):
        try:
            value = float(value)
        except ValueError:
            return set()
        return self.compare(value, operator)

    def compare(self, value, operator):
        if operator == '=':
            return set([
                idx for idx, entry_value in self.index_mapping.items()
                if entry_value == value
            ])
        elif operator == '>':
            return set([
                idx for idx, entry_value in self.index_mapping.items()
                if entry_value >= value
            ])
        elif operator == '<':
            return set([
                idx for idx, entry_value in self.index_mapping.items()
                if entry_value <= value
            ])


class DateTimeField(NumericField):
    """ A field with date-times. """

    DATETIME_FORMATS = [
        "%Y:%m:%d",
        "%H:%M:%S"
    ]

    def __init__(self, full_name, abbr_name, entry_mapping):
        super().__init__(full_name, abbr_name, entry_mapping)
        self.type = str

    def datetime_to_unix(self, dt_string: str):
        for frmt in DateTimeField.DATETIME_FORMATS:
            try:
                return time.mktime(
                    dt.datetime.strptime(dt_string, frmt).timetuple()
                )
            except (ValueError, OverflowError):
                pass
        return 0

    def reset_entries(self, entries: dict):
        """ Calls the base-class method, then converts every string datetime in
        the index_mapping to a UNIX-time number.
        """
        super().reset_entries(entries)
        for k, value in self.index_mapping.items():
            self.index_mapping[k] = self.datetime_to_unix(str(value))

    def get_entry_set(self, value, operator='='):
        try:
            value = self.datetime_to_unix(str(value))
        except ValueError:
            return set()
        return super().compare(value, operator)


class ListField(Field):
    """ A field with list values.
    """
    def __init__(self, full_name, abbr_name, entry_mapping):
        super().__init__(full_name, abbr_name, entry_mapping)
        self.type = list

    def reset_entries(self, entries: dict):
        """ Calls the base-class method, then converts every list-of-values in
        the index_mapping to a set-of-strings. These sets can then be compared
        to a query value consisting of a comma-delimited list of values.
        (see below).
        """
        super().reset_entries(entries)
        for k, value in self.index_mapping.items():
            self.index_mapping[k] = {str(x) for x in value}

    def get_entry_set(self, value, operator='?'):
        """
        Parameters
        ----------
        value: str
            A comma-delimited set of values.
        operator: str
            ! - the passed set must be equivalent to the entry's set.
            ? - the passed set must be a sub-set of the entry's set.

        Returns
        -------
        set
            The indices of the matching entries.
        """
        # split the value list into a set.
        value = str(value)
        value = set(value.split(','))
        print(value)

        if operator == '!':
            return set([
                idx for idx, entry_value in self.index_mapping.items()
                if value == entry_value
            ])
        elif operator == '?':
            return set([
                idx for idx, entry_value in self.index_mapping.items()
                if value <= entry_value
            ])
