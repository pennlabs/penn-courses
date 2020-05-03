import re
from datetime import datetime

from lark import Lark, Transformer
from tqdm import tqdm


"""
This file contains functionality for parsing the SQL dump files that we get from ISC.
The previous import script loaded these files into a MySQL database and then read them out
from SQL in queries in order to load them in as Django models. That's a lot of levels of indirection
and potential latency that made it hard to reason about what the import script was actually doing.

The dumps are in a very regular format and use a very limited subset of SQL. My first thought was
to use Regular Expressions to pick out keys and values, but going through all of the casing to
support commas _inside_ of quoted strings would have been extremely messy, if not downright
impossible due to regular expressions's inability to deal with recursive structures.

Parsers allow you to describe nested patterns more complex than RegEx can. We're using Lark,
a parser library for Python, to convert table rows into Python dictionaries where the key is
the column name and the value is the SQL value.

If you're interested in learning a ton more about parsing and related concepts, take CIS341!
Luckily, to understand what's going on for this small parser below, this tutorial for
parsing JSON is more than sufficient:
https://github.com/lark-parser/lark/blob/master/docs/json_tutorial.md
"""


sql_dump_parser = Lark(
    r"""
    ?value: string
          | SIGNED_NUMBER      -> number
          | date
          | TOKEN

    list : "(" [value ("," value)*] ")"

    row: "Insert into "i TOKEN list "Values"i list ";" // `""i` makes strings case insensitive

    date: "TO_DATE"i "(" string "," string ")"

    string : /'([^']|(''))*'/

    TOKEN: /[_A-Za-z0-9.]+/

    %import common.SIGNED_NUMBER
    %import common.WS
    %ignore WS
""",
    start="row",
)


class SQLDumpTransformer(Transformer):
    """
    This class transforms the Abstract Syntax Tree (AST) generated by the parser
    into a usable Python object.
    """

    def list(self, items):
        """
        List of values should just be a Python list.
        """
        return list(items)

    def row(self, items):
        """
        We have the keys and values that have already been parsed,
        simply zip them into a tuple list and then turn them into a dict
        to generate a row in a quasi-JSON format. Who needs MongoDB?
        """
        _, col_names, values = items
        return dict(zip(col_names, values))

    def TOKEN(self, items):
        """
        A token simply represents itself.
        """
        return items[:]

    def string(self, s):
        (s,) = s
        # Strip off whitespace from a string, and un-escape single quotes.
        return s[1:-1].strip().replace("''", "'")

    def number(self, n):
        (n,) = n
        return float(n)

    def date(self, items):
        """
        The dump includes the format (parsed at items[1] in this function),
        but it's not the same parse tokens that Python uses. From observation,
        all the dates are in the same format. If that changes, and dates start
        being off, here's a good place to look.
        """
        return datetime.strptime(items[0], "%m/%d/%Y %H:%M:%S")


class TypeTransformer(SQLDumpTransformer):
    """
    An alternative transformer for debugging and analysis that simply resolves
    terminals into their SQL types based on the literal. This was useful for
    reverse-engineering the schema from the dumps.
    """

    def string(self, s):
        return "STRING"

    def number(self, n):
        return "NUMBER"

    def date(self, items):
        return "DATE"


def parse_row(s, T=SQLDumpTransformer):
    """
    Given a string representing a single row, parse the row and transform
    it to a Python object with the given transformer.
    """
    tree = sql_dump_parser.parse(s)
    row = T().transform(tree)
    return row


def process_file(fo, process_row=None, T=SQLDumpTransformer, progress=True):
    """
    Read in and parse a SQL dump, with each row as a Python dictionary.
    tqdm shows a progress bar in the shell, and the process_row callback
    is used to collect the resulting Python objects from the parser.

    The `progess` option ensures we're piping the progress bar to the right
    place, and not just always polluting sys.stderr.
    """
    regex = re.compile(
        r"Insert into [\w\.]*\W*\(([\n ,\w]*)\)\W*Values\W*\((['\w, \&\n.:/\(\)!?$%*]*)\);"
    )
    contents = fo.read()
    matches = list(regex.finditer(contents))
    for x in tqdm(matches, disable=(not progress)):
        row = parse_row(x.group(), T)
        if process_row is not None:
            process_row(row)


def load_sql_dump(fo, progress=True):
    """
    Synchronously return all the rows from the database, in dictionary format.
    """
    data = list()
    process_file(fo, lambda row: data.append(row), progress=progress)
    return data
