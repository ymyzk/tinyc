#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

try:
    from llvm.core import Builder, Constant, Module, Type
    from llvm.core import IPRED_EQ, IPRED_NE, IPRED_SGE, IPRED_SGT, IPRED_SLE, IPRED_SLT
except:
    pass

from tinyc import token
from tinyc.analyzer import Analyzer
from tinyc.common import Kinds


class LLVMGenerator(Analyzer):
    def __init__(self):
        self.nbranch = 0
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
            'EQ': IPRED_EQ,
            'NEQ': IPRED_NE,
            'LT': IPRED_SLT,
            'LTE': IPRED_SLE,
            'GT': IPRED_SGT,
            'GTE': IPRED_SGE
        }
        self.op_logical = {
            'LAND': '',
            'LOR': ''
        }
        self.types = {
            'bool': Type.int(1),
            'int': Type.int(32)
        }
        self.undefined_functions = {}
        self.returns = {}

    def _new_label(self, prefix='label'):
        self.nlabel += 1
        return("L_{0}".format(self.nlabel))

    def analyze(self, ast, optimize=True):
        self.optimize = optimize
        self.module = Module.new('module')
        ast.accept(self)
        return self.module

    def a_ExternalDeclarationList(self, node):
        u"""先にグローバル変数をまとめて処理し, 次に関数定義を処理する"""
        # グローバル変数
        for external_declaration in node.nodes:
            if isinstance(external_declaration, token.Declaration):
                for declarator in external_declaration.declarators.nodes:
                    declarator.identifier.gv = self.module.add_global_variable(
                        self.types['int'], declarator.identifier.name, 0)
        # 関数定義 (コード)
        for external_declaration in node.nodes:
            if isinstance(external_declaration, token.FunctionDefinition):
                external_declaration.accept(self)

    def a_FunctionDefinition(self, node):
        # モジュールに関数を追加
        function = self.module.add_function(
            Type.function(
                self.types['int'],
                (self.types['int'],) * len(node.parameter_type_list.nodes)),
            node.declarator.identifier.name)
        node.declarator.identifier.ir = function

        entry = function.append_basic_block(
            'entry_' + node.declarator.identifier.name)
        self.builder = Builder.new(entry)

        # 戻り値を格納するためのメモリを確保
        self.returns[function] = (self.builder.alloca(self.types['int']), [],)

        # パラメータをメモリに割り当て
        for i, arg in enumerate(node.parameter_type_list):
            function.args[i].name = arg.declarator.identifier.name
            arg.declarator.identifier.memory = self.builder.alloca(self.types['int'])
            self.builder.store(function.args[i], arg.declarator.identifier.memory)

        # 関数本体のコード生成
        node.compound_statement.accept(self)

        return_block = function.append_basic_block(
            'return_' + node.declarator.identifier.name)

        self.builder.branch(return_block)
        self.builder.position_at_end(return_block)
        return_value = self.returns[function][0]
        ir = self.builder.load(return_value, 'return')
        self.builder.ret(ir)

        # 適切な場所に return を配置する
        for block in self.returns[function][1]:
            if not block.instructions[-1].is_terminator:
                self.builder.position_at_end(block)
                self.builder.branch(return_block)

    def a_Declarator(self, node):
        node.identifier.memory = self.builder.alloca(self.types['int'])

    def a_IfStatement(self, node):
        then_returned = else_returned = False

        # 条件判定のコード
        node.expr.accept(self)
        ir = self.builder.icmp(
            IPRED_NE, node.expr.ir, Constant.int(self.types['int'], 0))

        function = self.builder.basic_block.function

        then_block = function.append_basic_block(self._new_label())
        else_block = function.append_basic_block(self._new_label())

        # 条件分岐点
        self.builder.cbranch(ir, then_block, else_block)

        # then のコード生成, then 内で return されたかをチェックする
        self.builder.position_at_end(then_block)
        nbranch = self.nbranch
        node.then_statement.accept(self)
        if nbranch != self.nbranch:
            then_returned = True
        self.nbranch = nbranch
        then_block = self.builder.basic_block

        # else のコード生成, else 内で return されたかをチェックする
        self.builder.position_at_end(else_block)
        if not node.else_statement.is_null():
            node.else_statement.accept(self)
            if nbranch != self.nbranch:
                else_returned = True
            self.nbranch = nbranch
        else_block = self.builder.basic_block

        done_block = function.append_basic_block(self._new_label())

        # then, else それぞれについて, 内部で return されていなければ,
        # then -> done, else -> done のジャンプを設定
        if not then_returned:
            self.builder.position_at_end(then_block)
            self.builder.branch(done_block)
        if not else_returned:
            self.builder.position_at_end(else_block)
            self.builder.branch(done_block)
        self.builder.position_at_end(done_block)

    def a_ReturnStatement(self, node):
        self.nbranch += 1  # then. else 節内での分岐を検知
        function = self.builder.basic_block.function
        node.expr.accept(self)
        # return を配置したいブロックを覚えておく
        return_value = self.returns[function][0]
        self.returns[function][1].append(self.builder.basic_block)
        self.builder.store(node.expr.ir, return_value)

    def a_WhileLoop(self, node):
        function = self.builder.basic_block.function

        test_block = function.append_basic_block(self._new_label())
        loop_block = function.append_basic_block(self._new_label())

        self.builder.branch(test_block)
        self.builder.position_at_end(test_block)
        node.expr.accept(self)

        ir = self.builder.icmp(
            IPRED_EQ, node.expr.ir, Constant.int(self.types['int'], 0))

        self.builder.position_at_end(loop_block)
        node.statement.accept(self)
        self.builder.branch(test_block)

        done_block = function.append_basic_block(self._new_label())
        self.builder.position_at_end(test_block)
        self.builder.cbranch(ir, done_block, loop_block)
        self.builder.position_at_end(done_block)

    def a_FunctionExpression(self, node):
        if node.function.kind == Kinds.undefined_function:
            if node.function.name in self.undefined_functions:
                node.function.ir = self.undefined_functions[node.function.name]
            else:
                node.function.ir = self.module.add_function(
                    Type.function(
                        self.types['int'],
                        (self.types['int'],) * len(node.argument_list.nodes)),
                    node.function.name)
                self.undefined_functions[node.function.name] = node.function.ir

        node.argument_list.accept(self)
        node.ir = self.builder.call(
            node.function.ir, map(lambda a: a.ir, node.argument_list.nodes))

    def a_Negative(self, node):
        node.expr.accept(self)
        node.ir = self.builder.neg(node.expr.ir)

    def a_Increment(self, node):
        node.expr.accept(self)
        node.ir = self.builder.add(
            node.expr.ir, Constant.int(self.types['int'], 1))
        self.builder.store(node.ir, node.expr.memory)

    def a_Decrement(self, node):
        node.expr.accept(self)
        node.ir = self.builder.sub(
            node.expr.ir, Constant.int(self.types['int'], 1))
        self.builder.store(node.ir, node.expr.memory)

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
        node.right.accept(self)
        node.left.accept(self)

        if node.op == 'ASSIGN':
            node.ir = node.right.ir
            ir = node.right.ir
        elif node.op == 'ASSIGN_PLUS':
            node.ir = self.builder.add(node.left.ir, node.right.ir)
            ir = node.ir
        elif node.op == 'ASSIGN_MINUS':
            node.ir = self.builder.sub(node.left.ir, node.right.ir)
            ir = node.ir

        if getattr(node.left, 'memory', None) is not None:
            self.builder.store(ir, node.left.memory)
        else:
            self.builder.store(ir, node.left.gv)

    def _a_BinaryOperator_arithmetic(self, node):
        node.right.accept(self)
        node.left.accept(self)
        if node.op == 'PLUS':
            node.ir = self.builder.add(node.left.ir, node.right.ir)
        elif node.op == 'MINUS':
            node.ir = self.builder.sub(node.left.ir, node.right.ir)
        elif node.op == 'MULT':
            node.ir = self.builder.mul(node.left.ir, node.right.ir)
        elif node.op == 'DIV':
            node.ir = self.builder.sdiv(node.left.ir, node.right.ir)

    def _a_BinaryOperator_compare(self, node):
        node.right.accept(self)
        node.left.accept(self)
        comparator = self.op_compare[node.op]
        result = self.builder.icmp(comparator, node.left.ir, node.right.ir)
        node.ir = self.builder.zext(result, self.types['int'])

    def _a_BinaryOperator_logical(self, node):
        function = self.builder.basic_block.function
        result = self.builder.alloca(self.types['int'])
        if node.op == 'LAND':
            self.builder.store(Constant.int(self.types['int'], 0), result)
            node.left.accept(self)
            left_ir = self.builder.icmp(
                IPRED_EQ, node.left.ir, Constant.int(self.types['int'], 0))
            left_block = self.builder.basic_block

            right_block = function.append_basic_block(self._new_label())
            self.builder.position_at_end(right_block)
            node.right.accept(self)
            right_ir = self.builder.icmp(
                IPRED_EQ, node.right.ir, Constant.int(self.types['int'], 0))

            true_block = function.append_basic_block(self._new_label(''))
            self.builder.position_at_end(true_block)
            self.builder.store(Constant.int(self.types['int'], 1), result)

            done_block = function.append_basic_block(self._new_label())
            self.builder.position_at_end(left_block)
            self.builder.cbranch(left_ir, done_block, right_block)
            self.builder.position_at_end(right_block)
            self.builder.cbranch(right_ir, done_block, true_block)
            self.builder.position_at_end(true_block)
            self.builder.branch(done_block)
            self.builder.position_at_end(done_block)

        elif node.op == 'LOR':
            self.builder.store(Constant.int(self.types['int'], 1), result)
            node.left.accept(self)
            left_ir = self.builder.icmp(IPRED_EQ, node.left.ir, Constant.int(self.types['int'], 0))
            left_block = self.builder.basic_block

            right_block = function.append_basic_block(self._new_label())
            self.builder.position_at_end(right_block)
            node.right.accept(self)
            right_ir = self.builder.icmp(IPRED_EQ, node.right.ir, Constant.int(self.types['int'], 0))

            false_block = function.append_basic_block(self._new_label())
            self.builder.position_at_end(false_block)
            self.builder.store(Constant.int(self.types['int'], 0), result)

            done_block = function.append_basic_block(self._new_label())
            self.builder.position_at_end(left_block)
            self.builder.cbranch(left_ir, right_block, done_block)
            self.builder.position_at_end(right_block)
            self.builder.cbranch(right_ir, false_block, done_block)
            self.builder.position_at_end(false_block)
            self.builder.branch(done_block)
            self.builder.position_at_end(done_block)

        node.ir = self.builder.load(result)

    def a_Identifier(self, node):
        if getattr(node, 'memory', None) is not None:
            node.ir = self.builder.load(node.memory)
        else:
            node.ir = self.builder.load(node.gv)

    def a_Constant(self, node):
        node.ir = Constant.int(self.types['int'], node.value)
