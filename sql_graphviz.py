#!/usr/bin/env python

import html
import sys
from datetime import datetime
from pyparsing import (
    alphas,
    alphanums,
    CaselessLiteral,
    Word,
    Forward,
    OneOrMore,
    ZeroOrMore,
    CharsNotIn,
    Suppress,
    QuotedString,
    Optional
)


def field_act(s, loc, tok):
    fieldName = tok[0].replace('"', '')
    fieldSpec = html.escape(' '.join(tok[1::]).replace('"', '\\"'))
    # Don't try and format this HTML text string - DOT files are whitespace sensitive
    return '''<tr><td bgcolor="grey96" align="left" port="{0}"><font face="Times-bold"> {0} </font></td><td align="left" port="{0}_right"><font color="#535353"> {1} </font></td></tr>'''.format(fieldName, fieldSpec)


def field_list_act(s, loc, tok):
    return "\n        ".join(tok)


def create_table_act(s, loc, tok):
    # Don't try and format this HTML text string - DOT files are whitespace sensitive
    return '''
    "{tableName}" [
    shape=none
    label=<
      <table border="0" cellspacing="0" cellborder="1">
        <tr><td bgcolor="lightblue2" colspan="2"><font face="Times-bold" point-size="20"> {tableName} </font></td></tr>
        {fields}
      </table>
    >];'''.format(**tok)


def add_fkey_act(s, loc, tok):
    return "\n".join(
        '  "{tableName}":{keyName}_right -> "{fkTable}":{fkCol}'.format(**{
            **tok,
            "keyName": tok['keyName'][i],
            "fkCol": tok['fkCol'][i],
        })
        for i in range(0, len(tok['keyName']))
    )


def other_statement_act(s, loc, tok):
    return ""


def join_string_act(s, loc, tok):
    return "".join(tok).replace('\n', '\\n')


def quoted_default_value_act(s, loc, tok):
    return tok[0] + " " + "".join(tok[1::])


def grammar():
    parenthesis = Forward()
    parenthesis <<= "(" + ZeroOrMore(CharsNotIn("()") | parenthesis) + ")"
    parenthesis.setParseAction(join_string_act)

    quoted_string = "'" + OneOrMore(CharsNotIn("'")) + "'"
    quoted_string.setParseAction(join_string_act)

    quoted_default_value = (CaselessLiteral("DEFAULT")
        + quoted_string
        + OneOrMore(CharsNotIn(", \n\t")))
    quoted_default_value.setParseAction(quoted_default_value_act)

    field_def = OneOrMore(quoted_default_value
        | Word(alphanums + "_\"'`:-/[].")
        | parenthesis)
    field_def.setParseAction(field_act)

    tablename_def = (Word(alphanums + "`_.") | QuotedString("\""))

    field_list_def = field_def + ZeroOrMore(Suppress(",") + field_def)
    field_list_def.setParseAction(field_list_act)

    create_table_def = (CaselessLiteral("CREATE")
        + Optional(CaselessLiteral("UNLOGGED"))
        + CaselessLiteral("TABLE")
        + Optional(CaselessLiteral("IF NOT EXISTS"))
        + tablename_def.setResultsName("tableName")
        + "(" + field_list_def.setResultsName("fields") + ")"
        + ";")
    create_table_def.setParseAction(create_table_act)

    delete_restrict_action = (CaselessLiteral("CASCADE")
        | CaselessLiteral("RESTRICT")
        | CaselessLiteral("NO ACTION")
        | ( CaselessLiteral("SET")
            + ( CaselessLiteral("NULL") | CaselessLiteral("DEFAULT") )))

    fkey_cols = (
        Word(alphanums + "._")
        + ZeroOrMore(Suppress(",") + Word(alphanums + "._"))
    )

    add_fkey_def = (CaselessLiteral("ALTER")
        + CaselessLiteral("TABLE")
        + Optional(CaselessLiteral("ONLY"))
        + tablename_def.setResultsName("tableName")
        + CaselessLiteral("ADD")
        + CaselessLiteral("CONSTRAINT")
        + (Word(alphanums + "_") | QuotedString("\""))
        + CaselessLiteral("FOREIGN")
        + CaselessLiteral("KEY")
        + Optional(CaselessLiteral("IF NOT EXISTS"))
        + "(" + fkey_cols.setResultsName("keyName") + ")"
        + CaselessLiteral("REFERENCES") + tablename_def.setResultsName("fkTable")
        + "(" + fkey_cols.setResultsName("fkCol") + ")"
        + Optional(CaselessLiteral("DEFERRABLE"))
        + Optional(CaselessLiteral("ON") + "UPDATE" + delete_restrict_action)
        + Optional(CaselessLiteral("ON") + "DELETE" + delete_restrict_action)
        + ";")
    add_fkey_def.setParseAction(add_fkey_act)

    other_statement_def = OneOrMore(CharsNotIn(";")) + ";"
    other_statement_def.setParseAction(other_statement_act)

    comment_def = "--" + ZeroOrMore(CharsNotIn("\n"))
    comment_def.setParseAction(other_statement_act)

    return OneOrMore(
        comment_def
        | create_table_def
        | add_fkey_def
        | other_statement_def
    )


def graphviz(filename):
    print("/*")
    print(" * Graphviz of '%s', created %s" % (filename, datetime.now()))
    print(" * Generated from https://github.com/rm-hull/sql_graphviz")
    print(" */")
    print("digraph g { graph [ rankdir = \"LR\" ];")

    for i in grammar().setDebug(False).parseFile(filename):
        if i != "":
            print(i)
    print("}")

if __name__ == '__main__':
    filename = sys.stdin if len(sys.argv) == 1 else sys.argv[1]
    graphviz(filename)
