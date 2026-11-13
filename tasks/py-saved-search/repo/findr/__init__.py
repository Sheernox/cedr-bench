"""findr: a small search language over records, with saved searches.

Typical use::

    from findr.parser import parse
    from findr.match import search

    hits = search(parse('status:open -owner:"ben k"'), records)
"""

__version__ = "3.2.0"
