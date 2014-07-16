#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals
import logging


try:
    from llvm import passes
except:
    pass

from tinyc import analyzer, generator, optimizer
from tinyc.code import Label
from tinyc.parser import Parser


class Compiler(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.logger = logging.getLogger()

        # 字句解析器/構文解析器
        self.parser = Parser()
        self.parser.build(debug=kwargs['debug'])

        self.errors = 0
        self.warnings = 0
        self.optimized = 0

    def _analyze(self, analyzer, ast):
        ast = analyzer.analyze(ast)
        self.errors += analyzer.errors
        self.warnings += analyzer.warnings
        return ast

    def _optimize_llvm(self, module):
        manager = passes.PassManager.new()
        # manager.add(str('loop-unroll'))
        manager.run(module)

        manager = passes.FunctionPassManager.new(module)
        manager.add(str('adce'))
        manager.add(str('dce'))
        manager.add(str('die'))
        manager.add(str('dse'))
        manager.add(str('mem2reg'))
        manager.add(str('block-placement'))

        # Global Value Numbering
        manager.add(str('gvn'))
        # Reassociate expressions
        manager.add(str('reassociate'))
        # Combine redundant instructions
        manager.add(str('instcombine'))
        # Simplify the CFG
        manager.add(str('simplifycfg'))
        for i in range(5):
            for function in module.functions:
                manager.run(function)
        return module

    def _optimize_nasm(self, code):
        """最適化処理"""
        self.logger.info('Compilation process (Peephole optimizations)')
        for i in range(1, 6):
            self.logger.info('Peephole optimizations (Phase {0})'.format(i))
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
            self.logger.info('Optimized: {0}'.format(self.optimized - temp))
        return code

    def _optimize_one(self, optimizer, code):
        code = optimizer.optimize(code)
        self.optimized += optimizer.optimized
        return code

    def _format_llvm(self, module):
        self.logger.info('Compilation process (Code formatting)')
        # LLVM のモジュールを文字列に変換
        ir = str(module).split('\n')
        # common を llvmpy が出力してくれないので, external で出力したものを置換する
        ir = map(lambda i: i.replace(' external global i32', ' common global i32 0'), ir)
        ir = '\n'.join(ir)
        return ir

    def _format(self, code):
        """コードを文字列にフォーマットする処理"""
        self.logger.info('Compilation process (Code formatting)')
        result = []
        for line in code:
            if isinstance(line, Label):
                result.append(str(line) + ':')
            else:
                result.append(str(line))
        return "\n".join(result) + '\n'

    def compile(self, code):
        fm = self.kwargs['format']
        optimize = self.kwargs['optimization'] > 0
        result = {}

        self.logger.info('Compilation options')
        self.logger.info('* Format: ' + self.kwargs['format'])
        self.logger.info(
            '* Optimization level: ' + str(self.kwargs['optimization']))

        # 字句解析/構文解析
        self.logger.info('Compilation process (Lexical/Syntax analysis)')
        ast = self.parser.parse(code, optimize=optimize)
        self.errors = self.parser.errors
        self.optimized += self.parser.optimized

        if self.errors == 0:
            # 意味解析
            self.logger.info('Compilation process (Semantic analysis)')
            ast = self._analyze(analyzer.SymbolAnalyzer(), ast)
            ast = self._analyze(analyzer.SymbolReplaceAnalyzer(), ast)
            ast = self._analyze(analyzer.FunctionAnalyzer(), ast)
            ast = self._analyze(analyzer.ParameterAnalyzer(), ast)
            ast = self._analyze(analyzer.RegisterAnalyzer(), ast)

        if self.errors == 0:
            # コード生成
            self.logger.info('Compilation process (Code generation)')

            if fm == 'llvm':
                gen = generator.LLVMGenerator()
                module = gen.analyze(ast, optimize=optimize)

                if optimize:
                    module = self._optimize_llvm(module)

                result['asm'] = self._format_llvm(module)
            else:
                gen = generator.NASMx86Generator()
                ast = gen.analyze(ast, format=fm, optimize=optimize)
                code = gen.code
                self.optimized = gen.optimized

                # 最適化
                if optimize:
                    code = self._optimize_nasm(code)

                result['asm'] = self._format(code)

        # 抽象構文木
        if self.kwargs['ast']:
            self.logger.info('Compilation process (AST formatting)')
            result['ast'] = analyzer.PrintAnalyzer().analyze(ast)

        result['errors'] = self.errors
        result['warnings'] = self.warnings
        result['optimized'] = self.optimized

        return result
