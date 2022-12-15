# Python Resume
These are samples of python code I have written for various projects over the last few years.

Some of the sample were written as part of a commercial project. In these cases, the code
is fairly generic - it doesn't reveal anything about the project or infringe on any IP.

## PubMed Parser

This code allows you to search a database with queries of the form,
```  
>20[age] and (Jam*[name] or Charles[name]) and (>1.5[height] and <1.6[height])
```
that are used in applications like [PubMed](https://pubmed.ncbi.nlm.nih.gov).

The query is first parsed with code based on *Getting Started with PyParsing* (Paul McGuire, 2008, O'Reilly Media). The parsed query can then be converted into either a SQL query or used to search a document (JSON) database.

Since writing this code over a wet weekend I have used it in multiple commercial projects. Pretty much all applications need some search functionality but using a parser of the type implemented here has several advantages:

- The UI is very simple - just a query bar over a table of search results.
- New fields (name, height, age, etc) can be added with a couple of lines of code. In my code specifically, by creating a new instance of `Field`.
- Search can be extended to different types of database by simply adding one-line methods to the `UnaryOperation` and `BinaryOperation` classes.

Contrast this with the "hand crafted" approach I have seen in many commercial projects.
For each field there is separate UI element (often containing multiple subwidgets) and backend function, making for a very crowded and unaesthetic UI and codebase. Implementing boolean operations is hard and implementing S-expressions (bracketed boolean expressions) almost impossible, without a lot of very hacky code.





