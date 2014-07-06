#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""字句解析と構文解析で用いるキーワードやトークンをまとめたモジュール"""

from __future__ import unicode_literals

import enum


KEYWORDS = {
    # Keywords
    'else':     'ELSE',
    'if':       'IF',
    'int':      'INT',
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
    'EQUALS',    # =
    'PLUS_EQ',   # +=
    'MINUS_EQ',  # -=

    # Literals
    'ID',        # identifiers
    'CONSTANT',  # constant (int)

    # Delimiters
    'LPAREN',       # (
    'RPAREN',       # )
    'LBRACE',       # {
    'RBRACE',       # }
    'COMMA',        # ,
    'SEMICOLON',    # ;
) + tuple(KEYWORDS.values())


class Kinds(enum.Enum):
    """Identifier の種類を表す enum"""
    fresh = 0
    variable = 1
    function = 2
    parameter = 3
    undefined_function = 4
    function_call = 5
