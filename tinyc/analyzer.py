#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals
import sys

import enum

from tinyc import token
from tinyc.common import Kinds


class Analyzer(object):
    """汎用意味解析器"""
    def __init__(self):
        self.warnings = 0
        self.errors = 0

    def _analyze_list(self, l):
        map(lambda i: i.accept(self), l)

    def analyze(self, ast):
        ast.accept(self)
        return ast

    def warning(self, message):
        self.warnings += 1
        message = "Warning: {0}".format(message)
        print(message, file=sys.stderr)

    def error(self, message):
        self.errors += 1
        message = "Error: {0}".format(message)
        print(message, file=sys.stderr)

    def a_Node(self, node):
        pass

    def a_NodeList(self, node):
        self._analyze_list(node.nodes)

    def a_UnaryOperator(self, node):
        node.expr.accept(self)

    def a_BinaryOperator(self, node):
        node.left.accept(self)
        node.right.accept(self)

    def a_FunctionDefinition(self, node):
        node.parameter_type_list.accept(self)
        node.compound_statement.accept(self)

    def a_CompoundStatement(self, node):
        node.declaration_list.accept(self)
        node.statement_list.accept(self)

    def a_Declaration(self, node):
        node.declarators.accept(self)

    def a_ParameterDeclaration(self, node):
        node.declarator.accept(self)

    def a_Declarator(self, node):
        pass

    def a_IfStatement(self, node):
        node.expr.accept(self)
        node.then_statement.accept(self)
        node.else_statement.accept(self)

    def a_WhileLoop(self, node):
        node.expr.accept(self)
        node.statement.accept(self)

    def a_ReturnStatement(self, node):
        node.expr.accept(self)

    def a_FunctionExpression(self, node):
        node.function.accept(self)
        node.argument_list.accept(self)


class PrintAnalyzer(Analyzer):
    def __init__(self):
        self._indent = 0
        self._indent_amount = 2

    def indent(self):
        self._indent += 1

    def unindent(self):
        self._indent -= 1

    def write(self, s):
        self.text += (' ' * (self._indent_amount * self._indent) + s + '\n')

    def write_node(self, node):
        self.write('+ ' + node.__class__.__name__)

        for key in node.__dict__.keys():
            if key[0] == '_':
                continue
            val = node.__dict__[key]
            if isinstance(val, str) or isinstance(val, int):
                self.write('  %s: %s' % (key, str(val)))
            elif isinstance(val, Kinds):
                self.write('  %s: %s' % (key, str(val.name)))

    def write_subnode(self, subnode, label):
        if not subnode.is_null():
            self.write('  %s:' % label)
            self.indent()
            subnode.accept(self)
            self.unindent()

    def a_FunctionDefinition(self, node):
        self.write_node(node)
        self.write_subnode(node.declarator, 'Declarator')
        self.write_subnode(node.parameter_type_list, 'Paremeter type list')
        self.write_subnode(node.compound_statement, 'Compound statement')

    def a_UnaryOperator(self, node):
        self.write_node(node)
        self.write_subnode(node.expr, 'Expression')

    def a_BinaryOperator(self, node):
        self.write_node(node)
        self.write_subnode(node.left, 'Left')
        self.write_subnode(node.right, 'Right')

    def a_Declarator(self, node):
        self.write_node(node)
        self.write_subnode(node.identifier, 'Identifier')

    def a_Declaration(self, node):
        self.write_node(node)
        self.write_subnode(node.declarators, 'Declarator list')

    def a_ParameterDeclaration(self, node):
        self.write_node(node)
        self.write_subnode(node.declarator, 'Declarator')

    def a_NodeList(self, node):
        self.write_node(node)
        self.indent()
        self._analyze_list(node.nodes)
        self.unindent()

    def a_ParameterTypeList(self, node):
        self.write_node(node)
        self.indent()
        self._analyze_list(node.nodes)
        self.unindent()

    def a_CompoundStatement(self, node):
        self.write_node(node)
        self.write_subnode(node.declaration_list, 'Declaration list')
        self.write_subnode(node.statement_list, 'Statement list')

    def a_IfStatement(self, node):
        self.write_node(node)
        self.write_subnode(node.expr, 'Expression')
        self.write_subnode(node.then_statement, 'Then statement')
        self.write_subnode(node.else_statement, 'Else statement')

    def a_ReturnStatement(self, node):
        self.write_node(node)
        self.write_subnode(node.expr, 'Expression')

    def a_WhileLoop(self, node):
        self.write_node(node)
        self.write_subnode(node.expr, 'Expression')
        self.write_subnode(node.statement, 'Statement')

    def a_FunctionExpression(self, node):
        self.write_node(node)
        self.write_subnode(node.function, 'Function')
        self.write_subnode(node.argument_list, 'Argument list')

    def a_Identifier(self, node):
        self.write_node(node)

    def a_Constant(self, node):
        self.write_node(node)

    def analyze(self, ast):
        self.text = ''
        ast.accept(self)
        return self.text


class SymbolTable(object):
    class SymbolRedeclarationError(Exception):
        pass

    class SymbolConflictError(Exception):
        pass

    class SymbolShadowsParameterWarning(Exception):
        pass

    def __init__(self, parent=None, level=0):
        self.symbols = {}
        self.parent = parent
        # self.children = []
        self.level = level
        # if parent is not None:
        #     self.parent.children.append(self)

    def add(self, name, symbol):
        # 全てのテーブルからシンボルを探す
        if symbol.kind == Kinds.variable:
            self._add_variable(name, symbol)
        elif symbol.kind == Kinds.parameter:
            self._add_parameter(name, symbol)
        elif symbol.kind == Kinds.function:
            self._add_function(name, symbol)

    def _add_variable(self, name, symbol):
        temp = self.get(name)

        if temp is not None:
            # 変数名が何らかのシンボルとしてすでに定義されているとき
            if temp.kind == Kinds.variable:
                # 変数名がすでに定義されている時
                if name in self.symbols:
                    # 同一レベルで同じ変数名が使われているとき
                    raise self.SymbolRedeclarationError()
            elif temp.kind in (Kinds.function, Kinds.undefined_function):
                # 変数名が関数名または未定義関数名として使われているとき
                raise self.SymbolConflictError()
            elif temp.kind == Kinds.parameter:
                # 変数名がパラメータ名とかぶっているとき
                self._add_symbol(name, symbol)
                raise self.SymbolShadowsParameterWarning()

        self._add_symbol(name, symbol)

    def _add_parameter(self, name, symbol):
        if name in self.symbols:
            if self.symbols[name].kind == Kinds.parameter:
                # 同一レベルで同じパラメータ名が使われているとき
                raise self.SymbolRedeclarationError()

        self._add_symbol(name, symbol)

    def _add_function(self, name, symbol):
        if name in self.symbols:
            if self.symbols[name].kind in (Kinds.variable, Kinds.function):
                # 同一レベルで同じ名前の関数または変数があるとき
                raise self.SymbolRedeclarationError()

        self._add_symbol(name, symbol)

    def _add_symbol(self, name, symbol):
        symbol.level = self.level
        self.symbols[name] = symbol

    def get(self, name):
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent is not None:
            return self.parent.get(name)
        else:
            return None


class SymbolAnalyzer(Analyzer):
    def a_FunctionDefinition(self, node):
        node.declarator.identifier.kind = Kinds.function
        self._add_symbol(node.declarator.identifier)
        self._push_table(node)
        node.parameter_type_list.accept(self)
        node.compound_statement.accept(self)
        self._pop_table()

    def a_CompoundStatement(self, node):
        self._push_table(node)
        node.declaration_list.accept(self)
        node.statement_list.accept(self)
        self._pop_table()

    def a_Declaration(self, node):
        for declarator in node.declarators:
            declarator.identifier.kind = Kinds.variable
        node.declarators.accept(self)

    def a_ParameterDeclaration(self, node):
        node.declarator.identifier.kind = Kinds.parameter
        node.declarator.accept(self)

    def a_Declarator(self, node):
        self._add_symbol(node.identifier)

    def a_IfStatement(self, node):
        node.expr.accept(self)
        node.then_statement.accept(self)
        node.else_statement.accept(self)

    def a_FunctionExpression(self, node):
        node.function.kind = Kinds.function_call
        node.function.accept(self)
        node.argument_list.accept(self)

    def a_Identifier(self, node):
        # シンボルを検索する
        symbol = self.current_table.get(node.name)

        if node.kind == Kinds.function_call:
            if symbol is not None:
                if symbol.kind in (Kinds.function, Kinds.undefined_function):
                    # 関数のシンボルが見つかればシンボルの場所を記録
                    node.symbol = symbol
                else:
                    node.kind = Kinds.fresh
                    message = "Line {line}: '{value}' is not a function."
                    self.error(message.format(
                        line=node.lineno, value=node.name))
            else:
                # 関数のシンボルが見つからない場合は, 未定義関数のシンボルをテーブルに追加
                node.kind = Kinds.undefined_function
                self._add_symbol(node, table=self.root_table)
                message = "Line {line}: Undeclared function '{value}'."
                self.warning(message.format(
                    line=node.lineno, value=node.name))
        elif node.kind == Kinds.fresh:
            if symbol is not None:
                if symbol.kind in (Kinds.variable, Kinds.parameter):
                    # 変数またはパラメータのシンボルが見つかればシンボルの場所を記録
                    node.symbol = symbol
                else:
                    node.kind = Kinds.fresh
                    message = "Line {line}: '{value}' is not a variable."
                    self.error(message.format(
                        line=node.lineno, value=node.name))
            else:
                message = "Line {line}: Undeclared variable '{value}'."
                self.error(message.format(line=node.lineno, value=node.name))

    def _push_table(self, node):
        self.current_table = SymbolTable(
            self.current_table, level=self.current_table.level + 1)
        node.table = self.current_table

    def _pop_table(self):
        self.current_table = self.current_table.parent

    def _add_symbol(self, node, table=None):
        if table is None:
            table = self.current_table
        try:
            table.add(node.name, node)
        except SymbolTable.SymbolRedeclarationError:
            self.error(
                "Line {line}: Redeclaration of identifier '{value}'.".format(
                    line=node.lineno,
                    value=node.name))
        except SymbolTable.SymbolShadowsParameterWarning:
            msg = "Line {line}: Declaration of '{value}' shadows parameter."
            self.warning(msg.format(line=node.lineno, value=node.name))

    def analyze(self, ast):
        self.root_table = SymbolTable(level=0)
        self.current_table = self.root_table
        ast.current_table = self.root_table
        ast.accept(self)

        return ast


class SymbolReplaceAnalyzer(Analyzer):
    """Identifier.symbol に記録された symbol で Identifier を置換する"""
    def a_NodeList(self, node):
        node.nodes = map(self._replace_symbol, node.nodes)
        self._analyze_list(node.nodes)

    def a_UnaryOperator(self, node):
        node.expr = self._replace_symbol(node.expr)
        node.expr.accept(self)

    def a_BinaryOperator(self, node):
        node.left = self._replace_symbol(node.left)
        node.left.accept(self)
        node.right = self._replace_symbol(node.right)
        node.right.accept(self)

    def a_IfStatement(self, node):
        node.expr = self._replace_symbol(node.expr)
        node.expr.accept(self)
        node.then_statement.accept(self)
        node.else_statement.accept(self)

    def a_ReturnStatement(self, node):
        node.expr = self._replace_symbol(node.expr)
        node.expr.accept(self)

    def a_FunctionExpression(self, node):
        node.function = self._replace_symbol(node.function)
        node.function.accept(self)
        node.argument_list.accept(self)

    def _replace_symbol(self, node):
        if isinstance(node, token.Identifier):
            symbol = getattr(node, 'symbol', None)
            if symbol is not None:
                return symbol
        return node


class FunctionAnalyzer(Analyzer):
    """関数呼び出しのパラメータの数が正しいか解析する"""
    def a_FunctionDefinition(self, node):
        # 引数の数を identifier に記録
        parameters = len(node.parameter_type_list.nodes)
        node.declarator.identifier.parameters = parameters

        node.parameter_type_list.accept(self)
        node.compound_statement.accept(self)

    def a_FunctionExpression(self, node):
        # TODO: undefined_function の場合の処理を要チェック
        if node.function.kind == Kinds.function:
            if node.function.parameters != len(node.argument_list.nodes):
                message = "Line {line}: '{value}' requires {num} parameters."
                self.error(message.format(
                    line=node.lineno, value=node.function.name,
                    num=node.function.parameters))
        elif node.function.kind == Kinds.undefined_function:
            parameters = getattr(node.function, 'parameters', None)
            if parameters is None:
                node.function.parameters = len(node.argument_list.nodes)
            elif parameters != len(node.argument_list.nodes):
                message = "Line {line}: '{value}' requires {num} parameters."
                self.error(message.format(
                    line=node.lineno, value=node.function.name,
                    num=parameters))


class ParameterAnalyzer(Analyzer):
    """パラメータの EBP からの相対アドレスを計算する"""
    def a_ParameterTypeList(self, node):
        # パラメータリストが始まるたびに offset を初期化
        self.offset = 8
        map(lambda i: i.accept(self), node.nodes)

    def a_ParameterDeclaration(self, node):
        # パラメータの EBP からの offset を設定
        node.declarator.identifier.offset = self.offset
        self.offset += 4


class RegisterAnalyzer(Analyzer):
    """コード生成に必要なレジスタの数について見積もる"""
    def a_BinaryOperator(self, node):
        node.left.accept(self)
        node.right.accept(self)
        node.registers = 1

    def a_UnaryOperator(self, node):
        node.expr.accept(self)
        node.registers = 1

    def a_FunctionExpression(self, node):
        node.function.accept(self)
        node.argument_list.accept(self)
        node.registers = 1

    def a_Identifier(self, node):
        if node.kind in (Kinds.parameter, Kinds.variable):
            node.registers = 0

    def a_Constant(self, node):
        node.registers = 0
