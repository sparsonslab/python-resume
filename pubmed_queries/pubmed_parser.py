""" Parsing of boolean S-expressions.
"""
from functools import reduce
from itertools import chain

from pyparsing import (
    alphas, alphanums, nums, CaselessLiteral, Group, Literal, Word,
    oneOf, opAssoc, operatorPrecedence,
    ParseException, ParseSyntaxException,
    quotedString, removeQuotes,
)

from field import Field, DateTimeField


class PubMedParser:
    """ Parsing of Pubmed/NCBI-like search queries. e.g.

        Parsons[author] AND (>45[age] OR >100[iq])

    i) PubMedParser parses the query into a boolean S-expression of
    (field, value, operator) triples.
    ii) Each (field, value, operator) is passed to an appropriate Field object
    (see field.py) to retrieve a set of matching entries.
    iii) The matching set for each (field, value, operator) are combined
    by the booleans using Evaluator classes.

    Based on the code here:
    Getting Started with PyParsing, Paul McGuire, 2008 (O'Reilly Media)
    http://index-of.co.uk/Tutorials/Getting%20Started%20with%20Pyparsing.pdf

    Attributes
    ----------
    fields: [Field]
        The fields that can be searched.
    grammar: pyparsing.Forward
        The grammar that defines the parse.
    """
    def __init__(self, fields):

        # Field objects list
        self.fields = fields

        # search field
        field = Literal("[").suppress() - Word(alphas) - Literal(
            "]").suppress()

        # string search expression
        # ::= <search_term>[<field name>]
        str_srch = Group((Word(alphanums + '*') | quotedString.setParseAction(
            removeQuotes)) - field)
        str_srch.setParseAction(SearchString)

        # number (including date/time) search expression
        # ::= <operator><search_term>[<field name>]
        num_srch = Group(oneOf("> < =") - Word(nums + ':.-') - field)
        num_srch.setParseAction(SearchNumber)

        # list search expression
        # ::= <operator><search_term>[<field name>]
        lst_srch = Group(oneOf("! ?") - Word(alphanums + ',') - field)
        lst_srch.setParseAction(SearchList)

        # search expression
        all_srch = str_srch | num_srch | lst_srch

        # boolean, S-expression parsing
        and_ = CaselessLiteral("and")
        or_ = CaselessLiteral("or")
        not_ = CaselessLiteral("not")

        # grammar to parse
        self.grammar = operatorPrecedence(
            all_srch,
            [(not_, 1, opAssoc.RIGHT, SearchNot),
             (and_, 2, opAssoc.LEFT, SearchAnd),
             (or_, 2, opAssoc.LEFT, SearchOr)]
        )

    def _parse_query(self, query):
        """ Parse a PubMed-like query.

        Parameters
        ----------
        query: str
            The query.

        Returns
        -------
        field_names: [str]
            The names of the fields in the expression.
        parse_result: object
            Binary or Unary operator object at the top of the query tree,
            upon which can be called one of its methods.

        Raises
        ------
        PubMedParseException
            If the expression cannot be passed.
        """
        # check the query is balanced.
        if not balanced(query):
            raise PubMedParseException('', 'Is unbalanced')

        try:
            # parse
            parse_result = self.grammar.parseString(query)
            json = parse_result[0].to_json()

            # check all fields are valid
            field_names = get_key_values(json, 'field')
            not_matched_fields = Field.check_field_names(
                self.fields, field_names
            )
            if not_matched_fields:
                raise PubMedParseException(
                    '',
                    'Non-valid fields: ' + ', '.join(not_matched_fields)
                )
            return field_names, parse_result[0]
        except ParseSyntaxException as err:
            raise PubMedParseException(err, 'Cannot be parsed.')
        except ParseException as err:
            raise PubMedParseException(err, 'Cannot be parsed')

    def get_object_set(self, query):
        """ Get an object-set corresponding to a PubMed-like query.

        Returns
        -------
        []
            The set of entries matching the query or a set of unique-indices
            that can be mapped to the entries (see Field).
        """
        if not query:
            return self.fields[0].universal_set

        field_names, parse_result = self._parse_query(query)
        return parse_result.evaluate_expression(self.fields)

    def get_sql_query(self, query, table_name):
        """ Get a SQL expression corresponding to a PubMed-like query.

        Parameters
        ----------
        query: str
            PubMed-like query.
        table_name: str
            Name of the table to be searched.

        Returns
        -------
        str:
            SQL expression.
        """
        if not query:
            return [], f"SELECT * FROM {table_name}"

        field_names, parse_result = self._parse_query(query)
        sql = f"SELECT * FROM {table_name} WHERE " + parse_result.to_sql(self.fields)

        return field_names, sql


class PubMedParseException(Exception):
    """ General exception in parsing the query.
    """
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message

# -----------------------------------------------------------------------------
# Boolean evaluators
# -----------------------------------------------------------------------------


class UnaryOperation(object):
    def __init__(self, tokens):
        self.op, self.oper = tokens[0]


class SearchNot(UnaryOperation):

    def evaluate_expression(self, fields):
        return fields[0].universal_set - self.oper.evaluate_expression(fields)

    def to_json(self):
        return [{'bool': 'NOT'}, self.oper.to_json()]

    def to_sql(self, fields):
        return 'NOT ' + self.oper.to_sql(fields)


class BinaryOperation(object):

    def __init__(self, tokens):
        self.operands = tokens[0][0::2]


class SearchAnd(BinaryOperation):

    def evaluate_expression(self, fields):
        return reduce(
            lambda x, y: x & y,
            [oper.evaluate_expression(fields) for oper in self.operands]
        )

    def to_json(self):
        return list(chain.from_iterable(
            ({'bool': 'AND'}, oper.to_json()) for oper in self.operands
        ))

    def to_sql(self, fields):
        return "(" + " AND ".join(
            [oper.to_sql(fields) for oper in self.operands]
        ) + ")"


class SearchOr(BinaryOperation):

    def evaluate_expression(self, fields):
        return reduce(
            lambda x, y: x | y,
            [oper.evaluate_expression(fields) for oper in self.operands]
        )

    def to_json(self):
        return list(chain.from_iterable(
            ({'bool': 'OR'}, oper.to_json()) for oper in self.operands
        ))

    def to_sql(self, fields):
        return "(" + " OR ".join(
            [oper.to_sql(fields) for oper in self.operands]
        ) + ")"

# -----------------------------------------------------------------------------
# Field Evaluators
# -----------------------------------------------------------------------------


class SearchString:

    def __init__(self, tokens):
        self.term, self.field = tuple(tokens[0])

    def evaluate_expression(self, fields):
        return Field.get_field_entry_set(fields, self.field, self.term)

    def to_json(self):
        return {'field': self.field, 'term': self.term}

    def to_sql(self, fields):
        nom = Field.get_full_name(fields, self.field)
        term = self.term.replace("*", "%")
        return f"\"{nom}\" LIKE '{term}'"


class SearchNumber:

    def __init__(self, tokens):
        self.comp, self.term, self.field = tuple(tokens[0])

    def evaluate_expression(self, fields):
        return Field.get_field_entry_set(
            fields, self.field, self.term, self.comp
        )

    def to_json(self):
        return {
            'field': self.field, 'term': self.term, 'comparator': self.comp
        }

    def to_sql(self, fields):
        nom = Field.get_full_name(fields, self.field)
        if isinstance(Field.match_field(fields, self.field), DateTimeField):
            return f"\"{nom}\" {self.comp} '{self.term}'"
        else:
            return f"\"{nom}\" {self.comp} {self.term}"


class SearchList:

    def __init__(self, tokens):
        self.comp, self.term, self.field = tuple(tokens[0])

    def evaluate_expression(self, fields):
        return Field.get_field_entry_set(
            fields, self.field, self.term, self.comp
        )

    def to_json(self):
        return {
            'field': self.field, 'term': self.term, 'comparator': self.comp
        }

    def to_sql(self, fields):
        nom = Field.get_full_name(fields, self.field)
        # TODO - something here?
        return ""

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def get_key_values(obj, key_name):
    """ Get all values in a dictionary with the matching key, recursively
    (i.e. no matter how deep the key is, or how many times it occurs).

    Parameters
    ----------
    obj: dict
        The dictionary to search.
    key_name: Any
        The key for which to get values.

    Returns
    -------
    list
        Values corresponding to the key.
    """
    if isinstance(obj, dict):
        if key_name in obj:
            return [obj[key_name]]
    # search through lists...
    elif isinstance(obj, list):
        v = []
        for x in obj:
            v.extend(get_key_values(x, key_name))
        return v
    return []


def balanced(expr):
    """ Check whether an S-expression is balanced (filched from online).
    """
    brackets = ['()', '{}', '[]', '\'\'', '\"\"']
    my_string = ''.join([c for c in expr if c in '(){}[]\'\"'])
    while any(x in my_string for x in brackets):
        for br in brackets:
            my_string = my_string.replace(br, '')
    return not my_string
