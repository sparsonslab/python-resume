# Python Resume
These are samples of python code I have written for various projects over the last few years.

Some of the sample were written as part of a commercial project. In these cases, the code
is fairly generic - it doesn't reveal anything about the project or infringe on any IP.

## Query: Database Querying with a Uniform Syntax

In my academic days, before Google Scholar came along, I was a big user of [PubMed](https://pubmed.ncbi.nlm.nih.gov/) 
for searching through the scientific literature. I became very familiar with PubMed's query syntax - things of the sort:

``` parsons sp[au] and (intestine[title] or channel[title]) ```

When I was writing a search engine at my first industry job, I thought this would make a great interface. The UI would 
only need a single text box for inputting the query. I had seen too many times in UIs the following pattern. Each field 
is queried with a separate UI element(s), e.g. a text box for each string field, a check box for each boolean field, 
a text box and drop-down comparator for each numeric field. The fields can only be combined in limited ways 
(all OR or all AND) or else there has to be a bunch more UI elements for selecting AND, OR, NOT. Boolean expression can 
certainly not be combined in parentheses.

Implementing a simple PubMed-style query, requires a parser to parse the query. I came across the Pyparsing package 
which was included in some other package I was using (I can't remember which) and from there the booklet, "Getting 
started with Pyparsing" by Paul McGuire (2007, O'Reilly). A section of that book ("Parsing a search string") essentially 
gave me the code I was looking for. Perfect!

In this repository I have written an class (`Query`) that does the parsing outlined in McGuire. This is a base 
(abtract) class. It can be inherited from to implement the same PubMed-like query interface for different kinds 
of database. `ObjectListQuery(Query)` is used to query a list of objects of any type (class objects, 
dictionaries, etc.). `SQLQuery(Query)` is used to generate SQL queries. You can write your own subclass!


## Quantity: Dimensional analysis and equations of physical quantities

Physical equations usually involve quantities with both a value and units. The units represent the variable's
"dimension" in space, time and mass. Dimensional analysis involves making sure that the dimensions of quantities 
in an equation are commensurate when combined. That is when two quantities are added, subtracted or equated 
they have the same dimension. Also we often need to convert a quantity's value from one set of units to another.

Dimensional analysis and unit conversion by-hand is often a pain, especially when variables are raised 
by exponents and expressed in different, often non-base, units. To prevent headaches I wrote the `Quantity` class 
to represent a value and its units.
