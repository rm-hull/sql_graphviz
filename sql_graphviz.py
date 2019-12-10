#!/usr/bin/env python

import html
import sys
from datetime import datetime
from pyparsing import alphas, alphanums, Literal, Word, Forward, OneOrMore, ZeroOrMore, CharsNotIn, Suppress, QuotedString, Optional

class Field:

    def __init__(self, loc, tok):
        self.name = tok[0].replace('"', '')
        self.spec = html.escape(' '.join(tok[1::]).replace('"', '\\"'))

    def __str__(self):
        return '<tr><td bgcolor="grey96" align="left" port="{0}"><font face="Times-bold">{0}</font>  <font color="#535353">{1}</font></td></tr>'.format(self.name, self.spec)


class Table:

    def __init__(self, loc, tok):
        self.name = tok['tableName']
        self.fields = tok['fields']

    def __str__(self):
        return '''
        "{name}" [
        shape=none
        label=<
          <table border="0" cellspacing="0" cellborder="1">
            <tr><td bgcolor="lightblue2"><font face="Times-bold" point-size="20">{name}</font></td></tr>
            {fields}
          </table>
        >];'''.format(name=self.name, fields="\n        ".join(map(str, self.fields)))


class FKey:

    def __init__(self, loc, tok):
        self.table = tok['tableName']
        self.key = tok['keyName']
        self.ftable = tok['fkTable']
        self.fcol = tok['fkCol']

    def __str__(self):
        return '  "{table}":{key} -> "{ftable}":{fcol}'.format(
            table=self.table,
            key=self.key,
            ftable=self.ftable,
            fcol=self.fcol)


class OtherStatement:

    def __init__(self, s, loc, tok):
        pass

    def __str__(self):
        return ''

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

    quoted_default_value = "DEFAULT" + quoted_string + OneOrMore(CharsNotIn(", \n\t"))
    quoted_default_value.setParseAction(quoted_default_value_act)

    field_def = OneOrMore(quoted_default_value | Word(alphanums + "_\"'`:-/[].") | parenthesis)
    field_def.setParseAction(Field)

    tablename_def = ( Word(alphas + "`_.") | QuotedString("\"") )

    field_list_def = field_def + ZeroOrMore(Suppress(",") + field_def)

    create_table_def = Literal("CREATE") + "TABLE" + tablename_def.setResultsName("tableName") + "(" + field_list_def.setResultsName("fields") + ")" + ";"
    create_table_def.setParseAction(Table)

    add_fkey_def = Literal("ALTER") + "TABLE" + "ONLY" + tablename_def.setResultsName("tableName") + "ADD" + "CONSTRAINT" + Word(alphanums + "_") + "FOREIGN" + "KEY" + "(" + Word(alphanums + "_").setResultsName("keyName") + ")" + "REFERENCES" + Word(alphanums + "._").setResultsName("fkTable") + "(" + Word(alphanums + "_").setResultsName("fkCol") + ")" + Optional(Literal("DEFERRABLE")) + Optional(Literal("ON") + "DELETE" + ( Literal("CASCADE") | Literal("RESTRICT") )) + ";"
    add_fkey_def.setParseAction(FKey)

    other_statement_def = OneOrMore(CharsNotIn(";")) + ";"
    other_statement_def.setParseAction(OtherStatement)

    comment_def = "--" + ZeroOrMore(CharsNotIn("\n"))
    comment_def.setParseAction(OtherStatement)

    return OneOrMore(comment_def | create_table_def | add_fkey_def | other_statement_def)

def parse(filename):
    parsed = grammar().setDebug(False).parseFile(filename)
    return parsed

def graphviz(filename):
    print("/*")
    print(" * Graphviz of '%s', created %s" % (filename, datetime.now()))
    print(" * Generated from https://github.com/rm-hull/sql_graphviz")
    print(" */")
    print("digraph g { graph [ rankdir = \"LR\" ];")

    for stmt in parse(filename);
        if not isinstance(stmt, OtherStatement):
            print(stmt)
    print("}")

if __name__ == '__main__':
    filename = sys.stdin if len(sys.argv) == 1 else sys.argv[1]
    graphviz(filename)
