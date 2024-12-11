# Python Resume
These are samples of python code I have written for various projects over the last few years.

Some of the sample were written as part of a commercial project. In these cases, the code
is fairly generic - it doesn't reveal anything about the project or infringe on any IP.

## [Quantity](notebooks/quantities_and_units.ipynb): Dimensional analysis and equations of physical quantities

Physical equations usually involve quantities with both a value and units. The units represent the variable's
"dimension" in space, time and mass. Dimensional analysis involves (among other things) making sure that the dimensions of quantities 
in an equation are commensurate when combined. That is, when two quantities are added, subtracted or equated 
they have the same dimension. Also we often need to convert a quantity's value from one set of units to another. For example,
from 'derived' units to SI units.

Dimensional analysis and unit conversion by-hand is often a pain, especially when variables are raised 
by exponents and expressed in different, often non-base, units. To prevent headaches I wrote the [`Quantity`](resume/quantity/quantity.py) class 
to represent a value and its units.

## [Query](notebooks/query_with_uniform_syntax.ipynb): Database querying with a simple and uniform syntax

In my academic days, before Google Scholar came along, I was a big user of [PubMed](https://pubmed.ncbi.nlm.nih.gov/) 
for searching the scientific literature. I became very familiar with PubMed's query syntax - things of the sort:

``` parsons sp[au] and (intestine[title] or channel[title]) ```

When I was writing a search engine at my first industry job, I thought this would make a great interface. The UI would 
only need a single text box for inputting the query. I had seen too many times UIs with the following pattern. Each field 
is queried with a separate UI element, e.g. a text box for each string field, a check box for each boolean field, 
a text box and drop-down comparator for each numeric field. The fields can only be combined in limited ways 
(all OR or all AND) or else there has to be a bunch more UI elements for selecting AND, OR, NOT. Boolean expression can 
certainly not be combined in parentheses.

Implementing a simple PubMed-style query, requires a parser to parse the query. I came across the 
[Pyparsing package](https://pyparsing-docs.readthedocs.io/en/latest/index.html) which was included in some other package 
I was using (I can't remember which) and from there the booklet, "Getting  started with Pyparsing" by Paul McGuire 
(2007, O'Reilly). A section of that book ("Parsing a search string") essentially gave me the code I was looking for. Perfect!

In this repository I have written an class ([`Query`](resume/query/query.py)) that does the parsing outlined in McGuire. This is an 
abstract base class. `Query` is a  [data access object](https://en.wikipedia.org/wiki/Data_access_object) (DAO) - it provides access to a database
abstracted from the details of any particular database type. It can be inherited from to implement the same PubMed-like query interface for different kinds of 
database:
- [`ObjectListQuery(Query)`](resume/query/objectlistquery.py) is used to query a list of objects of any type (class objects, dictionaries, etc.). 
Fields are added simply, with a one-line specification. 
- [`SQLQuery(Query)`](resume/query/sqlquery.py) is used to generate SQL queries.
- [`MongoQuery(Query)`](resume/query/mongoquery.py) is used to generate MongoDB queries for PyMongo.
  
You can write your own subclass!

----
(C) Copyright 2017-2024 Sean Parsons, Cambridge, UK.
All rights reserved.
Permission to use, copy, modify, and distribute this software and its documentation for any purpose and without fee 
is hereby granted, provided that the above copyright notice appear in all copies and that both that copyright notice 
and this permission notice appear in supporting documentation.
