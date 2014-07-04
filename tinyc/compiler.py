#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals

from tinyc import analyzer, optimizer
from tinyc.code import Code, Comment, Label
from tinyc.generator import Generator
from tinyc.lexer import Lexer
from tinyc.parser import Parser


class Compiler(object):
    def __init__(self):
        # 字句解析器/構文解析器
        self.parser = Parser()
        self.parser.build()

        self.errors = 0
        self.warnings = 0
        self.optimized = 0

    def _analyze(self, analyzer, ast):
        ast = analyzer.analyze(ast)
        self.errors += analyzer.errors
        self.warnings += analyzer.warnings
        return ast

    def _optimize(self, code):
        for i in range(5):
            temp = self.optimized
            code = self._optimize_one(optimizer.LabelOptimizer(), code)
            code = self._optimize_one(optimizer.GlobalExternOptimizer(), code)
            code = self._optimize_one(optimizer.JumpOptimizer(), code)
            code = self._optimize_one(
                optimizer.UnnecessaryCodeOptimizer(), code)
            code = self._optimize_one(optimizer.ReplaceCodeOptimizer(), code)
            code = self._optimize_one(optimizer.StackPointerOptimzier(), code)
            if self.optimized == temp:
                break
        return code

    def _optimize_one(self, optimizer, code):
        code = optimizer.optimize(code)
        self.optimized += optimizer.optimized
        return code

    def _generate(self, code):
        result = []
        for line in code:
            if isinstance(line, Label):
                result.append(str(line) + ':')
            else:
                result.append(str(line))
        return "\n".join(result) + '\n'

    def compile(self, code, **kwargs):
        optimize = kwargs['O'] > 0
        # 字句解析/構文解析
        ast = self.parser.parse(code, optimize=optimize)
        self.errors = self.parser.errors
        self.optimized += self.parser.optimized

        if self.errors == 0:
            # 意味解析
            ast = self._analyze(analyzer.SymbolAnalyzer(), ast)
            ast = self._analyze(analyzer.SymbolReplaceAnalyzer(), ast)
            ast = self._analyze(analyzer.FunctionAnalyzer(), ast)
            ast = self._analyze(analyzer.ParameterAnalyzer(), ast)
            ast = self._analyze(analyzer.RegisterAnalyzer(), ast)

        if self.errors == 0:
            # コード生成
            generator = Generator()
            ast = generator.analyze(ast, optimize=optimize)
            code = generator.code
            self.optimized = generator.optimized

            # 最適化
            if optimize:
                code = self._optimize(code)
                result['optimized'] = self.optimized

            result['asm'] = self._generate(code)

        result = {
            'errors': self.errors,
            'warnings': self.warnings,
            'optimized': self.optimized
        }

        # 抽象構文木
        if kwargs['ast']:
            result['ast'] = analyzer.PrintAnalyzer().analyze(ast)

        return result
