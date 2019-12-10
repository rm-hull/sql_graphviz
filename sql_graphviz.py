#!/usr/bin/env python

import argparse
import html
import itertools
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
        self.outgoing = []
        self.incoming = []
        self.highlight = False

    def __str__(self):
        return '''
        "{name}" [
        shape=none
        label=<
          <table border="0" cellspacing="0" cellborder="1">
            <tr><td bgcolor="{color}"><font face="Times-bold" point-size="20">{name}</font></td></tr>
            {fields}
          </table>
        >];'''.format(name=self.name,
                      fields="\n        ".join(map(str, self.fields)),
                      color="red" if self.highlight else "lightblue2")


class FKey:

    def __init__(self, loc, tok):
        self.table = tok['tableName']
        self.key = tok['keyName']
        self.ftable = tok['fkTable']
        self.fcol = tok['fkCol']
        self.source = None
        self.target = None

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

def get_table(tables, name):
    res = tables.get(name)
    if res is None:
        warn('unknown table {!r}'.format(name))
    return res

def parse(filename):
    parsed = grammar().setDebug(False).parseFile(filename)
    tables = { table.name : table for table in filter(lambda s: isinstance(s, Table), parsed) }
    for fk in filter(lambda s: isinstance(s, FKey), parsed):
        fk.source = get_table(tables, fk.table)
        fk.target = get_table(tables, fk.ftable)
        if fk.source is not None and fk.target is not None:
            fk.source.outgoing.append(fk)
            fk.target.incoming.append(fk)
    return parsed, tables

def graphviz(filename, filter, filter_path):
    print("/*")
    print(" * Graphviz of '%s', created %s" % (filename, datetime.now()))
    print(" * Generated from https://github.com/rm-hull/sql_graphviz")
    print(" */")
    print("digraph g { graph [ rankdir = \"LR\" ];")

    parsed, tables = parse(filename)
    if filter is not None:
        marks = set()
        def print_connex(table):
            if id(table) in marks:
                return
            marks.add(id(table))
            print(table)
            for fk in itertools.chain(table.outgoing, table.incoming):
                if id(fk) not in marks:
                    marks.add(id(fk))
                    print(fk)
                    print_connex(fk.source)
                    print_connex(fk.target)
        for table in filter:
            table = get_table(tables, table)
            if table is not None:
                table.highlight = True
                print_connex(table)
    elif filter_path is not None:
        filter = set(filter_path)
        for f in filter:
            table = get_table(tables, f)
            if table is not None:
                table.highlight = True
        marks = set()
        def print_path(table, ends):
            path = table.name in ends
            if id(table) in marks:
                return path
            if path:
                if id(table) not in marks:
                    marks.add(id(table))
                    print(table)
                return True
            marks.add(id(table))
            for fk in table.outgoing:
                if print_path(fk.target, ends):
                    path = True
                    if id(fk) not in marks:
                        marks.add(id(fk))
                        print(fk)
            for fk in table.incoming:
                if print_path(fk.source, ends):
                    path = True
                    if id(fk) not in marks:
                        marks.add(id(fk))
                        print(fk)
            if path:
                print(table)
            return path
        for table in filter:
            table = get_table(tables, table)
            if table is not None:
                print_path(table, filter - set([table.name]))
    else:
        for stmt in parsed:
            if not isinstance(stmt, OtherStatement):
                print(stmt)

    print("}")

parser = argparse.ArgumentParser()
parser.add_argument('filename',
                    help='schema dump to parse, stdin by default',
                    nargs='?',
                    default=sys.stdin)
parser.add_argument('-f',
                    '--filter',
                    action='append',
                    help='show only given tables and related',
                    metavar='TABLE')
parser.add_argument('-p',
                    '--filter-path',
                    action='append',
                    help='show only tables on paths between given tables',
                    metavar='TABLE')
args = parser.parse_args()

if __name__ == '__main__':
    graphviz(args.filename, filter=args.filter, filter_path=args.filter_path)
