#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys

from ply import yacc

from tinyc import common
from tinyc.common import Kinds
from tinyc.lexer import Lexer


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


class Parser(object):
    u"""構文解析器"""
    tokens = common.TOKENS

    def p_program_external_declaration(self, p):
        """program : external_declaration"""
        p[0] = ExternalDeclarationList(p[1])

    def p_program_program_external_declaration(self, p):
        """program : program external_declaration"""
        p[1].add(p[2])
        p[0] = p[1]

    def p_external_declaration(self, p):
        """external_declaration : declaration
                                | function_definition"""
        p[0] = p[1]

    def p_declaration(self, p):
        """declaration : INT declarator_list SEMICOLON"""
        p[0] = Declaration(p[2])

    def p_declarator_list_declarator(self, p):
        """declarator_list : declarator"""
        p[0] = DeclaratorList(p[1])

    def p_declarator_list_declarator_list(self, p):
        """declarator_list : declarator COMMA declarator_list"""
        p[3].insert(0, p[1])
        p[0] = p[3]

    def p_declarator(self, p):
        """declarator : identifier"""
        p[0] = Declarator(p[1])

    def p_function_definition(self, p):
        """function_definition : INT declarator LPAREN parameter_type_list_opt RPAREN compound_statement"""
        p[0] = FunctionDefinition(p[2], p[4], p[6])

    def p_parameter_type_list_opt(self, p):
        """parameter_type_list_opt : empty
                                   | parameter_type_list"""
        if isinstance(p[1], NullNode):
            p[1] = ParameterTypeList()
        p[0] = p[1]

    def p_parameter_type_list_parameter_declaration(self, p):
        """parameter_type_list : parameter_declaration"""
        p[0] = ParameterTypeList(p[1])

    def p_parameter_type_list_parameter_type_list(self, p):
        """parameter_type_list : parameter_type_list COMMA parameter_declaration"""
        p[1].add(p[3])
        p[0] = p[1]

    def p_parameter_declaration(self, p):
        """parameter_declaration : INT declarator"""
        p[0] = ParameterDeclaration(p[2])

    def p_statement_semicolon(self, p):
        """statement : SEMICOLON"""
        pass

    def p_statement_expression(self, p):
        """statement : expression SEMICOLON"""
        p[0] = p[1]

    def p_statement_compound_statement(self, p):
        """statement : compound_statement"""
        p[0] = p[1]

    def p_statement_if(self, p):
        """statement : IF LPAREN expression RPAREN statement"""
        p[0] = IfStatement(p[3], p[5], NullNode())

    def p_statement_if_else(self, p):
        """statement : IF LPAREN expression RPAREN statement ELSE statement"""
        p[0] = IfStatement(p[3], p[5], p[7])

    def p_statement_while(self, p):
        """statement : WHILE LPAREN expression RPAREN statement"""
        p[0] = WhileLoop(p[3], p[5])

    def p_statement_return(self, p):
        """statement : RETURN expression SEMICOLON"""
        p[0] = ReturnStatement(p[2])

    def p_compound_statement_empty(self, p):
        """compound_statement : LBRACE RBRACE"""
        p[0] = CompoundStatement(NullNode(), NullNode())

    def p_compound_statement_declaration(self, p):
        """compound_statement : LBRACE declaration_list RBRACE"""
        p[0] = CompoundStatement(p[2], StatementList())

    def p_compound_statement_statement(self, p):
        """compound_statement : LBRACE statement_list RBRACE"""
        p[0] = CompoundStatement(DeclarationList(), p[2])

    def p_compound_statement_declaration_statement(self, p):
        """compound_statement : LBRACE declaration_list statement_list RBRACE"""
        p[0] = CompoundStatement(p[2], p[3])

    def p_declaration_list_declaration(self, p):
        """declaration_list : declaration"""
        p[0] = DeclarationList(p[1])

    def p_declaration_list_declaration_list(self, p):
        """declaration_list : declaration_list declaration"""
        p[1].add(p[2])
        p[0] = p[1]

    def p_statement_list_statement(self, p):
        """statement_list : statement"""
        p[0] = StatementList(p[1])

    def p_statement_list_statement_list(self, p):
        """statement_list : statement_list statement"""
        p[1].add(p[2])
        p[0] = p[1]

    def p_expression_assign_expr(self, p):
        """expression : assign_expr"""
        p[0] = p[1]

    def p_expression_expression(self, p):
        """expression : expression COMMA assign_expr"""
        p[1].add(p[3])
        p[0] = p[1]

    def p_assign_expr_or(self, p):
        """assign_expr : logical_OR_expr"""
        p[0] = p[1]

    def p_assign_expr_assign(self, p):
        """assign_expr : identifier EQUALS assign_expr"""
        p[0] = BinaryOperator('ASSIGN', p[1], p[3])

    def p_assign_expr_assign_plus(self, p):
        """assign_expr : identifier PLUS_EQ assign_expr"""
        p[0] = BinaryOperator('ASSIGN_PLUS', p[1], p[3])

    def p_assign_expr_assign_minus(self, p):
        """assign_expr : identifier MINUS_EQ assign_expr"""
        p[0] = BinaryOperator('ASSIGN_MINUS', p[1], p[3])

    def p_logical_OR_expr_and_expr(self, p):
        """logical_OR_expr : logical_AND_expr"""
        p[0] = p[1]

    def p_logical_OR_expr_or(self, p):
        """logical_OR_expr : logical_OR_expr LOR logical_AND_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] == Constant(1) or p[3] == Constant(1):
                p[0] = Constant(1)
            else:
                p[0] = Constant(0)
        else:
            p[0] = BinaryOperator('LOR', p[1], p[3])

    def p_logical_AND_expr_equality_expr(self, p):
        """logical_AND_expr : equality_expr"""
        p[0] = p[1]

    def p_logical_AND_expr_and(self, p):
        """logical_AND_expr : logical_AND_expr LAND equality_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] == Constant(1) and p[3] == Constant(1):
                p[0] = Constant(1)
            else:
                p[0] = Constant(0)
        else:
            p[0] = BinaryOperator('LAND', p[1], p[3])

    def p_equality_expr_relational_expr(self, p):
        """equality_expr : relational_expr"""
        p[0] = p[1]

    def p_equality_expr_eq(self, p):
        """equality_expr :  equality_expr EQ relational_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] == p[3]:
                p[0] = Constant(1)
            else:
                p[0] = Constant(0)
        else:
            p[0] = BinaryOperator('EQ', p[1], p[3])

    def p_equality_expr_neq(self, p):
        """equality_expr : equality_expr NEQ relational_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] != p[3]:
                p[0] = Constant(1)
            else:
                p[0] = Constant(0)
        else:
            p[0] = BinaryOperator('NEQ', p[1], p[3])

    def p_relational_expr_add(self, p):
        """relational_expr : add_expr"""
        p[0] = p[1]

    def p_relational_expr_lt(self, p):
        """relational_expr : relational_expr LT add_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] < p[3]:
                p[0] = Constant(1)
            else:
                p[0] = Constant(0)
        else:
            p[0] = BinaryOperator('LT', p[1], p[3])

    def p_relational_expr_lte(self, p):
        """relational_expr : relational_expr LTE add_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] <= p[3]:
                p[0] = Constant(1)
            else:
                p[0] = Constant(0)
        else:
            p[0] = BinaryOperator('LTE', p[1], p[3])

    def p_relational_expr_gt(self, p):
        """relational_expr : relational_expr GT add_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] > p[3]:
                p[0] = Constant(1)
            else:
                p[0] = Constant(0)
        else:
            p[0] = BinaryOperator('GT', p[1], p[3])

    def p_relational_expr_gte(self, p):
        """relational_expr : relational_expr GTE add_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] >= p[3]:
                p[0] = Constant(1)
            else:
                p[0] = Constant(0)
        else:
            p[0] = BinaryOperator('GTE', p[1], p[3])

    def p_add_expr_mult_expr(self, p):
        """add_expr : mult_expr"""
        p[0] = p[1]

    def p_add_expr_plus(self, p):
        """add_expr : add_expr PLUS mult_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            p[0] = p[1] + p[3]
        else:
            p[0] = BinaryOperator('PLUS', p[1], p[3])

    def p_add_expr_minus(self, p):
        """add_expr : add_expr MINUS mult_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            p[0] = p[1] - p[3]
        else:
            p[0] = BinaryOperator('MINUS', p[1], p[3])

    def p_mult_expr_unary_expr(self, p):
        """mult_expr : unary_expr"""
        p[0] = p[1]

    def p_mult_expr_mult(self, p):
        """mult_expr : mult_expr MULT unary_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            p[0] = p[1] * p[3]
        else:
            p[0] = BinaryOperator('MULT', p[1], p[3])

    def p_mult_expr_div(self, p):
        """mult_expr : mult_expr DIV unary_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            p[0] = p[1] / p[3]
        else:
            p[0] = BinaryOperator('DIV', p[1], p[3])

    def p_unary_expr_postfix(self, p):
        """unary_expr : postfix_expr"""
        p[0] = p[1]

    def p_unary_expr_minus(self, p):
        """unary_expr : MINUS unary_expr"""
        if self.optimize and self._check_if_constants(p[2]):
            self.optimized += 1
            p[0] = -p[2]
        else:
            p[0] = Negative(p[2])

    def p_unary_expr_increment(self, p):
        """unary_expr : INC identifier"""
        p[0] = Increment(p[2])

    def p_unary_expr_decrement(self, p):
        """unary_expr : DEC identifier"""
        p[0] = Decrement(p[2])

    def p_postfix_expr_primary_expr(self, p):
        """postfix_expr : primary_expr"""
        p[0] = p[1]

    def p_postfix_expr_fcall(self, p):
        """postfix_expr : identifier LPAREN argument_expression_list_opt RPAREN"""
        p[0] = FunctionExpression(p[1], p[3], p[1].lineno)

    def p_primary_expr(self, p):
        """primary_expr : identifier
                        | constant"""
        p[0] = p[1]

    def p_primary_expr_paren(self, p):
        """primary_expr : LPAREN expression RPAREN"""
        p[0] = p[2]

    def p_argument_expression_list_opt(self, p):
        """argument_expression_list_opt : empty
                                        | argument_expression_list"""
        if isinstance(p[1], NullNode):
            p[1] = ArgumentExpressionList()
        p[0] = p[1]

    def p_argument_expression_list_assign_expr(self, p):
        """argument_expression_list : assign_expr"""
        p[0] = ArgumentExpressionList(p[1])

    def p_argument_expression_list_argument_expression_list(self, p):
        """argument_expression_list : argument_expression_list COMMA assign_expr"""
        p[1].add(p[3])
        p[0] = p[1]

    def p_identifier(self, p):
        """identifier : ID"""
        p[0] = Identifier(p[1], p.lineno(1))

    def p_constant(self, p):
        """constant : CONSTANT"""
        p[0] = Constant(p[1])

    def p_empty(self, p):
        """empty : """
        p[0] = NullNode()

    def p_error(self, p):
        message = "Line {line}: Syntax error at '{value}'. "
        print(
            message.format(
                line=p.lineno,
                value=p.value),
            file=sys.stderr)

    # else は右結合的に処理する
    precedence = (
        ('right', 'ELSE',),
    )

    def _check_if_constants(self, *args):
        for arg in args:
            if not isinstance(arg, Constant):
                return False
        return True

    def build(self, **kwargs):
        self.optimized = 0
        self.lexer = Lexer()
        self.lexer.build()
        # kwargs['debug'] = True
        self.stack = []
        self.parser = yacc.yacc(module=self, **kwargs)

    def parse(self, data, optimize=True):
        self.optimize = optimize
        return self.parser.parse(data)
