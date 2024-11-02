# Python Resume
These are samples of python code I have written for various projects over the last few years.

Some of the sample were written as part of a commercial project. In these cases, the code
is fairly generic - it doesn't reveal anything about the project or infringe on any IP.

## PubMed Queries: Database search with parsed boolean expressions

This code allows you to search a database with queries of the form,
```  
>20[age] and (Jan*[name] or Charles[name]) and (>1.5[height] and <1.6[height])
```
that are used in applications like [PubMed](https://pubmed.ncbi.nlm.nih.gov). The square brackets specify a field - a column in a SQL table, a key in a hash-map or JSON-document, an attribute in a class instance. The field name doesn't need to be the same as the column/key/attribute name. There simply has to be a mapping between them and this mapping can be many to one, to allow abbreviated field names. Before the field is a condition for that field. The condition-field pairs are combined with boolean algebra and brackets ("S-expressions").

The query is first parsed with code based on *Getting Started with PyParsing* (Paul McGuire, 2008, O'Reilly Media). The parsed query is then either:
- translated into a query for a specific database type (e.g. SQL)
- used to search a collection of *any* type of object (JSON documents, python dictionaries, hash-maps, instances of your-favourite class, etc.) using the `Field` class.

Since writing this code over a wet weekend I have used it in multiple commercial projects. Pretty much all applications need some search functionality. Using a parser of the type implemented here has several advantages:

- The UI is very simple - just a query bar over a table of search results.
- New fields (name, height, age, etc) can be added with a couple of lines of code. In my code specifically, by creating a new instance of `Field`.
- Queries can be translated into other database formats (e.g. SQL) by simply adding one-line methods to the `UnaryOperation` and `BinaryOperation` classes.

Contrast this with the "hand crafted" approach I have often seen in commercial projects.
For each field there is a separate UI element (often containing multiple subwidgets) and backend function, making for a very crowded and unaesthetic UI and codebase. Implementing boolean operations is hard and implementing S-expressions almost impossible, without a lot of very hacky code.

## Quantity: Dimensional analysis and equations of physical quantities

Physical equations usually involve quantities with both a value and units. The units represent the variable's
"dimension" in space, time and mass. Dimensional analysis involves making sure that the dimensions of quantities 
in an equation are commensurate when combined. That is when two quantities are added, subtracted or equated 
they have the same dimension. Also we often need to convert a quantity's value from one set of units to another.

Dimensional analysis and unit conversion by-hand is often a pain, especially when variables are raised 
by exponents and expressed in different, often non-base, units. To prevent headaches I wrote the `Quantity` class 
to represent a value and its units.
