#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

from tinyc.common import Kinds


class Node(object):
    def is_null(self):
        return 0

    def as_tuple(self):
        return None

    def accept(self, analyzer):
        self._accept(self.__class__, analyzer)

    def _accept(self, klass, analyzer):
        # 解析器の a_<クラス名> のメソッドを検索して実行する
        # 存在しない場合はノードのスーパークラスを順に辿って探す
        # print('DEBUG:', klass.__name__)
        method = getattr(analyzer, "a_%s" % klass.__name__, None)
        if method is None:
            bases = klass.__bases__
            last = None
            for i in bases:
                last = self._accept(i, analyzer)
            return last
        else:
            return method(self)


class NullNode(Node):
    def is_null(self):
        return 1


class Identifier(Node):
    def __init__(self, name, lineno):
        self.name = name
        self.lineno = lineno
        self.kind = Kinds.fresh


class Constant(Node):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return self.value

    def __add__(self, other):
        return Constant(self.value + other.value)

    def __sub__(self, other):
        return Constant(self.value - other.value)

    def __mul__(self, other):
        return Constant(self.value * other.value)

    def __div__(self, other):
        if self.value > 0 and other.value > 0:
            return Constant(self.value // other.value)
        elif self.value > 0 and other.value > 0:
            return Constant(self.value // other.value)
        else:
            result = self.value // other.value
            mod = self.value % other.value
            if mod == 0:
                return Constant(result)
            else:
                return Constant(result + 1)

    def __neg__(self):
        return Constant(-self.value)

    def __eq__(self, other):
        return self.value == other.value

    def __ne__(self, other):
        return self.value != other.value

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value

    def __gt__(self, other):
        return self.value > other.value

    def __ge__(self, other):
        return self.value >= other.value


class Declaration(Node):
    def __init__(self, declarators):
        self.declarators = declarators


class ParameterDeclaration(Node):
    def __init__(self, declarator):
        self.declarator = declarator


class Declarator(Node):
    def __init__(self, identifier):
        self.identifier = identifier


class UnaryOperator(Node):
    def __init__(self, node):
        self.expr = node


class Negative(UnaryOperator):
    pass


class Increment(UnaryOperator):
    pass


class Decrement(UnaryOperator):
    pass


class BinaryOperator(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right


class IfStatement(Node):
    def __init__(self, expr, then_statement, else_statement):
        self.expr = expr
        self.then_statement = then_statement
        self.else_statement = else_statement


class ReturnStatement(Node):
    def __init__(self, expr):
        self.expr = expr


class WhileLoop(Node):
    def __init__(self, expr, statement):
        self.expr = expr
        self.statement = statement


class NodeList(Node):
    def __init__(self, node=None):
        if node is None:
            self.nodes = []
        else:
            self.nodes = [node]

    def __iter__(self):
        return self.nodes.__iter__()

    def add(self, node):
        self.nodes.append(node)

    def insert(self, index, node):
        self.nodes.insert(index, node)


class ExternalDeclarationList(NodeList):
    pass


class DeclaratorList(NodeList):
    pass


class ParameterTypeList(NodeList):
    pass


class DeclarationList(NodeList):
    pass


class StatementList(NodeList):
    pass


class ArgumentExpressionList(NodeList):
    pass


class FunctionExpression(Node):
    def __init__(self, function, argument_list, lineno=0):
        self.function = function
        self.argument_list = argument_list
        if lineno > 0:
            self.lineno = lineno


class CompoundStatement(Node):
    def __init__(self, declaration_list, statement_list):
        self.declaration_list = declaration_list
        self.statement_list = statement_list


class FunctionDefinition(Node):
    def __init__(self, declarator, parameter_type_list, compound_statement):
        self.declarator = declarator
        self.parameter_type_list = parameter_type_list
        self.compound_statement = compound_statement
