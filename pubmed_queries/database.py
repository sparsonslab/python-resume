from abc import ABCMeta, abstractmethod

from pyparsing import (
    alphas, alphanums, nums, CaselessLiteral, Group, Literal, Word,
    oneOf, opAssoc, operatorPrecedence,
    ParseException, ParseSyntaxException,
    quotedString, removeQuotes,
)


class DataBase(metaclass=ABCMeta):
    """ An searchable database.

    """
    def __init__(self):
        self.grammar = self._create_grammar()

    def query(self, query, *args, **kwargs):
        """ Make a query. """
        try:
            parse_result = self.grammar.parseString(query)
            return parse_result[0].evaluate(*args, **kwargs)
        except ParseSyntaxException:
            raise ValueError('The query cannot be parsed.')
        except ParseException:
            raise ValueError('The query cannot be parsed.')

    # -------------------------------------------------------------------------
    # Database specific search actions.
    # -------------------------------------------------------------------------

    @abstractmethod
    def search_not(self, operands):
        pass

    @abstractmethod
    def search_and(self, operands):
        pass

    @abstractmethod
    def search_or(self, operands):
        pass

    @abstractmethod
    def search_string(self, term, field):
        pass

    @abstractmethod
    def search_number(self, comp, term, field):
        pass

    @abstractmethod
    def search_list(self, comp, term, field):
        pass

    # -------------------------------------------------------------------------
    # Grammar creation
    # -------------------------------------------------------------------------

    def _create_grammar(self):
        """ Create the grammar for searching the database. """
        parent = self

        # Grammar objects
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
