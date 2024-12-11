#  (C) Copyright 2017-2024 Sean Parsons, Cambridge, UK.
#               All rights reserved.
#  Permission to use, copy, modify, and distribute this software and its
#  documentation for any purpose and without fee is hereby granted, provided
#  that the above copyright notice appear in all copies and that both that
#  copyright notice and this permission notice appear in supporting
#  documentation.
from abc import ABCMeta, abstractmethod
import datetime

from pyparsing import (
    alphas, alphanums, nums, CaselessLiteral, Group, Literal, Word,
    oneOf, opAssoc, operatorPrecedence,
    ParseException, ParseSyntaxException,
    quotedString, removeQuotes,
)


class Query(metaclass=ABCMeta):
    """ An interface for querying databases using boolean expressions.

    This class provides a uniform interface for querying any type of database,
    using the same query syntax. A concrete subclass for a particular
    database must override the abstract methods and (possibly) self.query().

    Boolean queries consist of "<comparator><search-term>[<field>]" inputs
    combined using boolean operators (AND, OR and NOT) and parentheses.
    e.g. To query a database of animals that begin with "z" or are green and
    have more than two legs, the query is,
    "(z*[name] OR green[color]) AND >2[legs]"

    Based upon the code of,
    McGuire (2007). Getting started with Pyparsing. O'Reilly.

    Attributes
    ----------
    grammar: pyparsing.Forward
        The grammar that defines the query syntax.
    """
    def __init__(self):
        self.grammar = self._create_grammar()

    def query(self, query):
        """ Make a query.

        Parameters
        ----------
        query: str
            A boolean query.

        Returns
        -------
        any:
            The search result. The type is that returned by the overridden
            abstract methods.
        """
        try:
            parse_result = self.grammar.parseString(query)
            return parse_result[0].evaluate()
        except ParseSyntaxException:
            raise ValueError('The query cannot be parsed.')
        except ParseException:
            raise ValueError('The query cannot be parsed.')

    # -------------------------------------------------------------------------
    # Operand evaluation methods.
    # -------------------------------------------------------------------------

    @abstractmethod
    def search_not(self, operand):
        """ Not operation.

        Parameters
        ----------
        operand:
            The operand to be combined with NOT.
            An instance of one of the operand classes defined inline
            in self._create_grammar(). e.g. SearchAnd, SearchString, etc.
        """
        pass

    @abstractmethod
    def search_and(self, operands):
        """ And operation.

        Parameters
        ----------
        operands:
            The operands to be combined with AND.
            Instances of one of the operand classes defined inline
            in self._create_grammar(). e.g. SearchNumber, SearchString, etc.
        """
        pass

    @abstractmethod
    def search_or(self, operands):
        """ Or operation.

        Parameters
        ----------
        operands:
            The operands to be combined with OR.
            Instances of one of the operand classes defined inline
            in self._create_grammar(). e.g. SearchNumber, SearchString, etc.
        """
        pass

    @abstractmethod
    def search_string(self, term, field):
        """ Search string operation.

        <search-term>[field]

        Parameters
        ----------
        term: str
            The search term. Can contain alphanumerics and '*'.
        field: str
            The field name.
        """
        pass

    @abstractmethod
    def search_number(self, comp, term, field):
        """ Search string operation.

        <comparator><search-term>[field]

        Parameters
        ----------
        comp: str
            The comparator. Must be <, > or =.
        term: str
            The search term. Can contain alphanumerics and ':', '.' and '-'.
        field: str
            The field name.
        """
        pass

    @abstractmethod
    def search_list(self, comp, term, field):
        """ Search string operation.

        <comparator><search-term>[field]

        Parameters
        ----------
        comp: str
            The comparator. Must be ! or ?.
        term: str
            The search term. Can contain alphanumerics and ',' (to delimit a list).
        field: str
            The field name.
        """
        pass

    # -------------------------------------------------------------------------
    # Grammar creation
    # -------------------------------------------------------------------------

    def _create_grammar(self):
        """ Create the grammar for searching the database. """
        parent = self

        # Operator classes.
        # These are defined inline so that they can access the overridden
        # abstract methods.
        class UnaryOperation:
            def __init__(self, tokens):
                self.op, self.oper = tokens[0]

        class SearchNot(UnaryOperation):

            def evaluate(self):
                return parent.search_not(self.oper)

        class BinaryOperation:

            def __init__(self, tokens):
                self.operands = tokens[0][0::2]

        class SearchAnd(BinaryOperation):

            def evaluate(self):
                return parent.search_and(self.operands)

        class SearchOr(BinaryOperation):

            def evaluate(self):
                return parent.search_or(self.operands)

        class SearchString:

            def __init__(self, tokens):
                self.term, self.field = tuple(tokens[0])

            def evaluate(self):
                return parent.search_string(self.term, self.field)

        class SearchNumber:

            def __init__(self, tokens):
                self.comp, self.term, self.field = tuple(tokens[0])

            def evaluate(self):
                return parent.search_number(self.comp, self.term, self.field)

        class SearchList:

            def __init__(self, tokens):
                self.comp, self.term, self.field = tuple(tokens[0])

            def evaluate(self):
                return parent.search_list(self.comp, self.term, self.field)

        # search field
        field = Literal("[").suppress() - Word(alphas) - Literal("]").suppress()

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
        return operatorPrecedence(
            all_srch,
            [(not_, 1, opAssoc.RIGHT, SearchNot),
             (and_, 2, opAssoc.LEFT, SearchAnd),
             (or_, 2, opAssoc.LEFT, SearchOr)]
        )


def convert_term_to_type(field: str, term: str, target_type, possible_types):
    """ Convert a string search term to a designated type.

    Gives a standard interpretation of types like datetime and boolean.

    Parameters
    ----------
    field: str
        The name of the field.
    term: str
        The search term for the field.
    target_type: Type
        The field type.
    possible_types: [Type]
        Possible field types for a string/number/list search.

    Returns
    -------
    Any
        The search term converted to the target type.

    Throws
    ------
    ValueError
        If the target type is not in the possible types or,
        the search term cannot be converted to the target type.
    """
    if target_type not in possible_types:
        tstr = ",".join([str(t) for t in possible_types])
        raise ValueError(f"Field {field} is not a {tstr}.")
    elif target_type == str:
        return term
    elif target_type == bool:
        return term.lower == "t"
    elif target_type in (float, int):
        try:
            return float(term)
        except ValueError:
            raise ValueError(f"Field {field}: {term} cannot be converted into a number.")
    elif target_type == datetime.datetime:
        try:
            # todo - allow different datetime formats?
            return datetime.datetime.strptime(term, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Field {field}: {term} cannot be converted into a date.")
    elif target_type == list:
        # todo - convert types in list?
        return term.split(",")
    return term
