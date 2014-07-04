#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import sys

from ply import lex

from tinyc import common


class Lexer(object):
    """字句解析器"""
    tokens = common.TOKENS

    t_PLUS      = r'\+'
    t_MINUS     = r'-'
    t_MULT      = r'\*'
    t_DIV       = r'/'
    t_LAND      = r'&&'
    t_LOR       = r'\|\|'
    t_EQ        = r'=='
    t_NEQ       = r'!='
    t_LT        = r'<'
    t_LTE       = r'<='
    t_GT        = r'>'
    t_GTE       = r'>='
    t_INC       = r'\+\+'
    t_DEC       = r'--'

    t_EQUALS    = r'='
    t_PLUS_EQ   = r'\+='
    t_MINUS_EQ  = r'-='

    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_LBRACE = r'\{'
    t_RBRACE = r'\}'
    t_COMMA  = r','
    t_SEMICOLON = r';'

    t_ignore = ' \t'

    def t_ID(self, t):
        r'[A-Za-z][A-Za-z0-9_]*'
        # すべての Identifier をこの関数で処理し, キーワードに含まれる場合は種類を変える
        t.type = common.KEYWORDS.get(t.value, 'ID')
        return t

    def t_CONSTANT(self, token):
        r'\d+'
        token.value = int(token.value)
        return token

    def t_newline(self, t):
        r'\n+'
        # デバッグ用に改行ごとに行番号をインクリメントする
        t.lexer.lineno += len(t.value)

    def t_comment(self, t):
        r'/\*[\w\W]*?\*/'
        t.lexer.lineno += t.value.count('\n')

    def t_error(self, t):
        self.errors += 1
        print(
            "Line {line}: Illegal character '{value}'.".format(
                line=t.lineno,
                value=t.value[0]),
            file=sys.stderr)
        t.lexer.skip(1)

    def build(self, **kwargs):
        self.errors = 0
        self.lexer = lex.lex(module=self, **kwargs)

    def input(self, data):
        return self.lexer.input(data)
