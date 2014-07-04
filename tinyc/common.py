#!/usr/bin/env python
# -*- coding: utf-8 -*-

import enum


KEYWORDS = {
    # Keywords
    'int':      'INT',
    'if':       'IF',
    'else':     'ELSE',
    'return':   'RETURN',
    'while':    'WHILE',
}

TOKENS = (
    # Operators
    'PLUS',     # +
    'MINUS',    # -
    'MULT',     # *
    'DIV',      # /
    'LAND',     # &&
    'LOR',      # ||
    'EQ',       # ==
    'NEQ',      # !=
    'LT',       # <
    'LTE',      # <=
    'GT',       # >
    'GTE',      # >=
    'INC',      # ++
    'DEC',      # --

    # Assignments
    'EQUALS',   # =
    'PLUS_EQ',  # +=
    'MINUS_EQ', # -=

    # Literals
    'ID',       # identifiers
    'CONSTANT', # constant (int)

    # Delimiters
    'LPAREN',       # (
    'RPAREN',       # )
    'LBRACE',       # {
    'RBRACE',       # }
    'COMMA',        # ,
    'SEMICOLON',    # ;
) + tuple(KEYWORDS.values())


class Kinds(enum.Enum):
    # 初期値
    fresh = 0
    variable = 1
    function = 2
    parameter = 3
    undefined_function = 4
    function_call = 5
