#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

from tinyc import token
from tinyc.analyzer import Analyzer
from tinyc.code import (
    Code, Comment, Common, Data, Extern, Global, Label, Memory, Registers,
    Section)
from tinyc.common import Kinds


class Generator(Analyzer):
    def __init__(self):
        self.code = []
        self.nlabel = 0
        self.op_assign = {
            'ASSIGN': '',
            'ASSIGN_PLUS': '',
            'ASSIGN_MINUS': ''
        }
        self.op_arithmetic = {
            'PLUS': 'add',
            'MINUS': 'sub',
            'MULT': 'imul',
            'DIV': 'idiv'
        }
        self.op_compare = {
            'EQ': 'sete',
            'NEQ': 'setne',
            'LT': 'setl',
            'LTE': 'setle',
            'GT': 'setg',
            'GTE': 'setge'
        }
        self.op_logical = {
            'LAND': '',
            'LOR': ''
        }
        self.op_commutative = {
            'PLUS': 'add',
            'MULT': 'imul',
            'EQ': 'sete',
            'NEQ': 'setne'
        }

    def _write(self, code, comment=None):
        self.code.append(code)

    def _write_code(self, op, *args, **kwargs):
        code = Code(op, *args, **kwargs)
        self._write(code)
        return code

    def _write_label(self, label, comment=None):
        if comment is not None:
            self._write(Comment(comment))
        self._write(label)

    def _write_comment(self, comment):
        self._write(Comment(comment))

    def _new_label(self, prefix='label'):
        self.nlabel += 1
        return Label("{0}_{1}".format(prefix, self.nlabel))

    def _allocate(self):
        self.last_alloc -= 4
        self.top_alloc = min(self.last_alloc, self.top_alloc)
        return Memory(Registers.ebp, self.last_alloc)

    def _release(self):
        self.last_alloc += 4
        return self.last_alloc

    def analyze(self, ast, optimize=True):
        self.optimize = optimize
        self.optimized = 0
        self.last_alloc = 0
        self.top_alloc = 0
        ast.accept(self)
        return ast

    def a_ExternalDeclarationList(self, node):
        """先にグローバル変数をまとめて処理し, 次に関数定義を処理する"""
        # グローバル変数
        for external_declaration in node.nodes:
            if isinstance(external_declaration, token.Declaration):
                for declarator in external_declaration.declarators.nodes:
                    label = Label('_' + declarator.identifier.name)
                    declarator.identifier.label = label
                    self._write(Global(label))
                    self._write(Common(label), 4)
        # 関数定義 (コード)
        self._write('')
        self._write(Section('text'))
        for external_declaration in node.nodes:
            if isinstance(external_declaration, token.FunctionDefinition):
                external_declaration.accept(self)

    def a_FunctionDefinition(self, node):
        label = Label('_' + node.declarator.identifier.name)
        self.return_label = Label(
            "return_{0}".format(node.declarator.identifier.name))
        self._write(Global(label))
        self._write('')
        self._write_label(label)
        self._write_code('push', Registers.ebp)
        self._write_code('mov', Registers.ebp, Registers.esp)
        code = self._write_code('sub', Registers.esp, 0)
        node.compound_statement.accept(self)
        # Nlocal の値を計算後にセット
        l = list(code.args)
        l[1] = -self.top_alloc
        code.args = tuple(l)
        self._write_label(self.return_label)
        self._write_code('mov', Registers.esp, Registers.ebp)
        self._write_code('pop', Registers.ebp)
        self._write_code('ret')
        self.top_alloc = 0

    def a_DeclarationList(self, node):
        for declaration in node.nodes:
            for declarator in declaration.declarators:
                declarator.identifier.offset = self._allocate().offset
                declarator.accept(self)

    def a_CompoundStatement(self, node):
        alloc = self.last_alloc
        node.declaration_list.accept(self)
        node.statement_list.accept(self)
        self.last_alloc = alloc

    def a_Negative(self, node):
        node.expr.accept(self)
        self._write_code('neg', Registers.eax, comment='negative')

    def a_Increment(self, node):
        var = self._get_identifier_address(node.expr)
        node.expr.accept(self)

        self._write_code('inc', Registers.eax, comment='increment')
        self._write_code(
            'mov', var, Registers.eax, comment='assign ' + node.expr.name)

    def a_Decrement(self, node):
        var = self._get_identifier_address(node.expr)
        node.expr.accept(self)

        self._write_code('dec', Registers.eax, comment='decrement')
        self._write_code(
            'mov', var, Registers.eax, comment='assign ' + node.expr.name)

    def a_BinaryOperator(self, node):
        if node.op in self.op_assign:
            self._a_BinaryOperator_assign(node)
        elif node.op in self.op_arithmetic:
            self._a_BinaryOperator_arithmetic(node)
        elif node.op in self.op_compare:
            self._a_BinaryOperator_compare(node)
        elif node.op in self.op_logical:
            self._a_BinaryOperator_logical(node)

    def _a_BinaryOperator_assign(self, node):
        var = self._get_identifier_address(node.left)
        node.right.accept(self)

        if node.op == 'ASSIGN_PLUS':
            self._write_code('add', Registers.eax, var, comment='add')
        elif node.op == 'ASSIGN_MINUS':
            self._write_code('neg', Registers.eax, comment='minus')
            self._write_code('add', Registers.eax, var, comment='minus')

        self._write_code(
            'mov', var, Registers.eax, comment='assign ' + node.left.name)

    def _a_BinaryOperator_arithmetic(self, node):
        if node.right.registers == 0:
            self._a_BinaryOperator_arithmetic_l(node)
        elif node.left.registers == 0 and node.right.registers == 1:
            if node.op in self.op_commutative:
                self._a_BinaryOperator_arithmetic_r(node)
            else:
                self._a_BinaryOperator_arithmetic_rsl(node)
        else:
            self._a_BinaryOperator_arithmetic_rsl(node)

    def _a_BinaryOperator_arithmetic_l(self, node):
        """Left 型"""
        # Left
        node.left.accept(self)
        # Right
        if isinstance(node.right, token.Constant):
            right = node.right.value
        elif isinstance(node.right, token.Identifier):
            right = self._get_identifier_address(node.right)
        else:
            raise Exception()
        # Calc
        if node.op == 'DIV':
            self._write_code('cdq')
            if isinstance(node.right, token.Identifier):
                self._write_code('idiv', right, comment='calc (L)')
            else:
                temp = self._allocate()
                self._write_code('mov', temp, right, comment='right temp')
                self._write_code('idiv', temp, comment='calc (L)')
                self._release()
        else:
            self._write_code(
                self.op_arithmetic[node.op], Registers.eax, right,
                comment='calc (L)')

    def _a_BinaryOperator_arithmetic_r(self, node):
        """Right 型"""
        # Right
        node.right.accept(self)
        # Left
        if isinstance(node.left, token.Constant):
            left = node.left.value
        elif isinstance(node.left, token.Identifier):
            left = self._get_identifier_address(node.left)
        else:
            raise Exception()
        # Calc
        if node.op == 'DIV':
            self._write_code('cdq')
            self._write_code('idiv', left, comment='calc (R)')
        else:
            self._write_code(
                self.op_arithmetic[node.op], Registers.eax, left,
                comment='calc (R)')

    def _a_BinaryOperator_arithmetic_rsl(self, node):
        """Right-Save-Left 型"""
        # Right
        node.right.accept(self)
        temp = self._allocate()
        self._write_code('mov', temp, Registers.eax, comment='right temp')
        # Left
        node.left.accept(self)
        # Calc
        if node.op == 'DIV':
            self._write_code('cdq')
            self._write_code('idiv', temp, comment='calc (RSL)')
        else:
            self._write_code(
                self.op_arithmetic[node.op], Registers.eax, temp,
                comment='calc (RSL)')
        self._release()

    def _a_BinaryOperator_compare(self, node):
        if node.right.registers == 0:
            self._a_BinaryOperator_compare_l(node)
        elif node.left.registers == 0 and node.right.registers == 1:
            if node.op in self.op_commutative:
                self._a_BinaryOperator_compare_r(node)
            else:
                self._a_BinaryOperator_compare_rsl(node)
        else:
            self._a_BinaryOperator_compare_rsl(node)

        self._write_code(
            self.op_compare[node.op], Registers.al, comment='set flag')
        self._write_code('movzx', Registers.eax, Registers.al)

    def _a_BinaryOperator_compare_l(self, node):
        """Left 型"""
        # Left
        node.left.accept(self)
        # Right
        if isinstance(node.right, token.Constant):
            right = node.right.value
        elif isinstance(node.right, token.Identifier):
            right = self._get_identifier_address(node.right)
        else:
            raise Exception()
        # Compare
        self._write_code('cmp', Registers.eax, right, comment='compare (L)')

    def _a_BinaryOperator_compare_r(self, node):
        """Right 型"""
        # Right
        node.right.accept(self)
        # Left
        if isinstance(node.left, token.Constant):
            left = node.left.value
        elif isinstance(node.left, token.Identifier):
            left = self._get_identifier_address(node.left)
        else:
            raise Exception()
        # Compare
        self._write_code('cmp', Registers.eax, left, comment='compare (R)')

    def _a_BinaryOperator_compare_rsl(self, node):
        """Right-Save-Left 型"""
        # Right
        node.right.accept(self)
        temp = self._allocate()
        self._write_code('mov', temp, Registers.eax, comment='right temp')
        # Left
        node.left.accept(self)
        # Compare
        self._write_code('cmp', Registers.eax, temp, comment='compare (RSL)')
        self._release()

    def _a_BinaryOperator_logical(self, node):
        if node.op == 'LAND':
            temp = self._allocate()
            label = self._new_label('and')
            self._write_code('mov', temp, 0, comment='false')

            node.left.accept(self)
            self._write_code('cmp', Registers.eax, temp, comment='is false?')
            self._write_code('je', label)

            node.right.accept(self)
            self._write_code('cmp', Registers.eax, temp, comment='is false?')
            self._write_code('je', label)

            self._write_code('mov', temp, 1, comment='true')
            self._write_label(label)
            self._write_code('mov', Registers.eax, temp, comment='logical and')
        elif node.op == 'LOR':
            temp = self._allocate()
            label = self._new_label('or')
            self._write_code('mov', temp, 1, comment='true')

            node.left.accept(self)
            self._write_code('cmp', Registers.eax, temp, comment='is true?')
            self._write_code('je', label)

            node.right.accept(self)
            self._write_code('cmp', Registers.eax, temp, comment='is true?')
            self._write_code('je', label)

            self._write_code('mov', temp, 0, comment='false')
            self._write_label(label)
            self._write_code('mov', Registers.eax, temp, comment='logical or')

    def a_IfStatement(self, node):
        else_label = self._new_label('if_else')
        done_label = self._new_label('if_done')
        node.expr.accept(self)
        if self.optimize and isinstance(node.expr, token.Constant):
            self.optimized += 1
            if node.expr == token.Constant(0):
                node.then_statement.accept(self)
            else:
                node.else_statement.accept(self)
        else:
            self._write_code('cmp', Registers.eax, 0, comment='compare (if)')
            if node.else_statement.is_null():
                self._write_code('je', done_label)
                node.then_statement.accept(self)
            else:
                self._write_code('je', else_label)
                node.then_statement.accept(self)
                self._write_code('jmp', else_label)
                self._write_label(else_label)
                node.else_statement.accept(self)
            self._write_label(done_label)

    def a_WhileLoop(self, node):
        test_label = self._new_label('while_test')
        done_label = self._new_label('while_done')
        self._write_label(test_label)
        node.expr.accept(self)
        self._write_code('cmp', Registers.eax, 0, comment='compare (while)')
        self._write_code('je', done_label)
        node.statement.accept(self)
        self._write_code('jmp', test_label)
        self._write_label(done_label)

    def a_FunctionExpression(self, node):
        label = Label('_' + node.function.name)
        if node.function.kind == Kinds.undefined_function:
            self._write(Extern(label))
        node.argument_list.accept(self)
        self._write_code('call', label)
        self._write_code(
            'add', Registers.esp, 4 * len(node.argument_list.nodes),
            comment='Release argument stack')

    def a_ArgumentExpressionList(self, node):
        l = len(node.nodes)
        for i, argument in enumerate(reversed(node.nodes)):
            if isinstance(argument, token.Constant):
                arg = argument.value
            elif (isinstance(argument, token.Identifier)
                    and hasattr(argument, 'offset')):
                print(argument.name)
                arg = Memory(Registers.ebp, argument.offset)
            else:
                argument.accept(self)
                arg = Registers.eax
            self._write_code('push', arg, comment='argument {0}'.format(l - i))

    def a_ReturnStatement(self, node):
        node.expr.accept(self)
        self._write_code('jmp', self.return_label)

    def a_Constant(self, node):
        self._write_code('mov', Registers.eax, node.value, comment='constant')

    def _get_identifier_address(self, identifier):
        offset = getattr(identifier, 'offset', None)
        if offset is None:
            return Data(identifier.label)
        else:
            return Memory(Registers.ebp, identifier.offset)

    def a_Identifier(self, node):
        offset = getattr(node, 'offset', None)
        if offset is None:
            self._write_code(
                'mov', Registers.eax, Data(node.label),
                comment='id (global): {0}'.format(node.label.label[1:]))
        else:
            self._write_code(
                'mov', Registers.eax, Memory(Registers.ebp, node.offset),
                comment='id: {0}'.format(node.name))
