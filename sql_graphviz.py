#!/usr/bin/python

import sys
from datetime import datetime
from pyparsing import alphas, alphanums, Literal, Word, Forward, \
                      OneOrMore, ZeroOrMore, CharsNotIn, Suppress


def field_act(s, loc, tok):
    return ("<" + tok[0] + "> " + " ".join(tok)).replace("\"", "\\\"")


def field_list_act(s, loc, tok):
    return " | ".join(tok)


def create_table_act(s, loc, tok):
    return """
  "%(tableName)s" [
    label="<%(tableName)s> %(tableName)s | %(fields)s"
    shape="record" fillcolor="lightblue2" style="filled"
  ];""" % tok


def add_fkey_act(s, loc, tok):
    return """  "%(tableName)s":%(keyName)s -> "%(fkTable)s":%(fkCol)s""" % tok


def other_statement_act(s, loc, tok):
    return ""


def grammar():
    parenthesis = Forward()
    parenthesis <<= "(" + ZeroOrMore(CharsNotIn("()") | parenthesis) + ")"

    field_def = OneOrMore(Word(alphanums + "_\"'`:-") | parenthesis)
    field_def.setParseAction(field_act)

    field_list_def = field_def + ZeroOrMore(Suppress(",") + field_def)
    field_list_def.setParseAction(field_list_act)

    create_table_def = Literal(
        "CREATE") + "TABLE" + Word(
        alphas + "`_").setResultsName(
        "tableName") + "(" + field_list_def.setResultsName(
        "fields") + ")" + ";"
    create_table_def.setParseAction(create_table_act)

    add_fkey_def = Literal(
        "ALTER") + "TABLE" + "ONLY" + Word(
        alphanums + "_").setResultsName(
        "tableName") + "ADD" + "CONSTRAINT" + Word(
        alphanums + "_") + "FOREIGN" + "KEY" + "(" + Word(
        alphanums + "_").setResultsName(
        "keyName") + ")" + "REFERENCES" + Word(
        alphanums + "_").setResultsName(
        "fkTable") + "(" + Word(
        alphanums + "_").setResultsName(
        "fkCol") + ")" + ";"
    add_fkey_def.setParseAction(add_fkey_act)

    other_statement_def = OneOrMore(CharsNotIn(";")) + ";"
    other_statement_def.setParseAction(other_statement_act)

    comment_def = "--" + ZeroOrMore(CharsNotIn("\n"))
    comment_def.setParseAction(other_statement_act)

    return OneOrMore(comment_def | create_table_def | add_fkey_def | other_statement_def)


def graphviz(filename):
    print """/*"""
    print """/* Graphviz of '%s', created %s """ % (filename, datetime.now())
    print """ * Generated from https://github.com/rm-hull/sql_graphviz"""
    print """ */"""
    print """digraph g { graph [ rankdir = "LR" ]; """

    for i in grammar().parseFile(filename):
        if i != "":
            print i
    print "}"

if __name__ == '__main__':
    filename = sys.stdin if len(sys.argv) == 1 else sys.argv[1]
    graphviz(filename)
