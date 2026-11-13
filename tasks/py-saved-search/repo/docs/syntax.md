# Search syntax

This page is the reference users get from the Help menu. It is a promise:
searches that follow it keep working across releases.

## Terms

| You type        | Finds records where                                   |
|-----------------|-------------------------------------------------------|
| `invoice`       | any field contains `invoice`                          |
| `status:open`   | the `status` field contains `open`                    |
| `size>10`       | the `size` field is a number greater than 10          |
| `size>=10`, `size<10`, `size<=10` | the same, with the other comparisons |

Matching ignores case. A field name is a letter or underscore followed by
letters, digits or underscores. Numbers are written with digits and an
optional decimal point; they are never negative.

## Combining terms

- Terms next to each other must all match. `AND` between them means the
  same thing.
- `OR` matches either side. `AND` binds tighter: `a b OR c` is `(a b) OR c`.
- `NOT term` or `-term` matches records the term does not match.
- Parentheses group.

`AND`, `OR` and `NOT` are keywords only in capitals; `and` is an ordinary
word.

## Values

A value can be typed bare when it is not empty, has no spaces and none of
`( ) : " < >`, does not start with `-`, and is not one of the keywords.
Anything else goes in double quotes.

Inside double quotes:

- `\"` is a double quote,
- `\\` is one backslash,
- a backslash before any other character stands for itself, so Windows
  paths can be typed as they are: `"C:\temp"` is `C:\temp`.

A quoted value with no closing quote is an error.

Examples:

```
path:"C:\Program Files\app"
title:"say \"hi\""
share:"\\\\fileserver\\scans"
-status:closed (owner:ana OR owner:"ben k")
```
