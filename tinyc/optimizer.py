#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""最適化用のクラスをまとめたモジュール"""

from __future__ import print_function, unicode_literals
import logging

from tinyc.code import (
    Code, Comment, Data, Extern, Global, Label, Memory, Register, Registers)


class Optimizer(object):
    def __init__(self):
        self.logger = logging.getLogger()
        self.optimized = 0

    def optimize(self, code):
        return code


class LabelOptimizer(Optimizer):
    """不要なラベルと削除することによる最適化"""

    def __init__(self):
        super(LabelOptimizer, self).__init__()
        self.replace_table = {}

    def _optimize_duplication(self, code):
        """重複するラベルの削除"""
        label = None

        # 重複しているラベルを見つけて, 置換表を作成する
        for line in code:
            if isinstance(line, Label):
                if label is None:
                    label = line
                elif line.glob:
                    # GLOBAL に用いるラベルは置換しない
                    continue
                else:
                    self.replace_table[line] = label
            elif isinstance(line, Comment):
                continue
            else:
                label = None

        # 重複するラベルの削除と置換
        new_code = []
        for line in code:
            if isinstance(line, Label):
                if line in self.replace_table:
                    # 重複するラベル宣言はコードから外す
                    self.logger.info(
                        'Remove: label dupulication: ' + line.label)
                    self.optimized += 1
                    continue
            elif isinstance(line, Code):
                new_args = []
                for arg in line.args:
                    if isinstance(arg, Label) and arg in self.replace_table:
                        # 置換対象のラベルを引数に見つければ置換する
                        self.optimized += 1
                        new_args.append(self.replace_table[arg])
                    else:
                        new_args.append(arg)
                line.args = new_args
            new_code.append(line)
        return new_code

    def _optimize_unused(self, code):
        """利用されていないラベルの削除"""
        unused = {}
        used = {}

        # 利用されていないラベルを見つける
        for i, line in enumerate(code):
            if isinstance(line, Label):
                if line not in used and not line.glob:
                    # 現時点で引数に利用されていないラベルであれば未使用に追加
                    # ただしグローバルで利用するものは削除しない
                    unused[line] = i
            elif isinstance(line, Code):
                # 引数でラベルが利用されている場合は使用中のラベルに追加
                labels = filter(lambda a: isinstance(a, Label), line.args)
                if len(labels) == 0:
                    continue
                for label in labels:
                    if label in unused:
                        del unused[label]
                    if label not in used:
                        used[label] = True

        self.optimized += len(unused)

        map(lambda l: self.logger.info('Remove: unused label: ' + l.label), unused)

        return [i for j, i in enumerate(code) if j not in unused.values()]

    def optimize(self, code):
        code = self._optimize_duplication(code)
        code = self._optimize_unused(code)
        return code


class GlobalExternOptimizer(Optimizer):
    """EXTERN の重複を取り除き, GLOBAL とともに先頭にまとめる"""
    def optimize(self, code):
        _globals = []
        externs = {}
        others = []
        new_code = []

        for line in code:
            if isinstance(line, Global):
                _globals.append(line)
            elif isinstance(line, Extern):
                # EXTERN が重複しないように追加していく
                if str(line) in externs:
                    self.logger.info(
                        'Remove: extern dupulication: ' + line.label.label)
                    self.optimized += 1
                else:
                    externs[str(line)] = line
            else:
                others.append(line)

        for gl in _globals:
            new_code.append(gl)
        for ex in externs:
            new_code.append(externs[ex])
        for line in others:
            new_code.append(line)

        return new_code


class JumpOptimizer(Optimizer):
    def _optimize_jump_1(self, code):
        """無条件ジャンプ後の実行されない不要な命令を削除"""
        new_code = []
        jump = False
        for line in code:
            if isinstance(line, Label):
                # ラベルが出てきたら削除区間終了
                jump = False
            elif jump:
                # 無条件ジャンプ直後の実行されないコードをスキップ
                self.optimized += 1
                self.logger.info('Remove: instruction after jmp')
                continue
            elif isinstance(line, Code):
                if line.op == 'jmp':
                    # 無条件ジャンプ命令を検出 -> 削除区間開始
                    jump = True
            new_code.append(line)
        return new_code

    def _optimize_jump_2(self, code):
        """直後のラベルへの無条件ジャンプ命令を削除"""
        jump = None
        jump_line = -1
        delete_lines = []
        for i, line in enumerate(code):
            if isinstance(line, Label):
                if jump is not None and line == jump.args[0]:
                    # 無条件ジャンプ命令直後のラベルであれば, ジャンプ命令を削除対象に追加
                    self.optimized += 1
                    delete_lines += [jump_line]
                    self.logger.info('Remove: unnecessary jmp')
                jump = None
            elif isinstance(line, Code):
                if line.op == 'jmp':
                    # 無条件ジャンプ命令を検出
                    jump = line
                    jump_line = i
                else:
                    jump = None
        return [i for j, i in enumerate(code) if j not in delete_lines]

    def optimize(self, code):
        code = self._optimize_jump_1(code)
        code = self._optimize_jump_2(code)
        return code


class UnnecessaryCodeOptimizer(Optimizer):
    """不要コードを削除する"""
    def _check_single_deletable(self, code):
        """コードを 1 行見て不要かどうか判定する"""
        if code.op in ('add', 'sub', 'imul',):
            if not isinstance(code.args[1], (int,)):
                return False
            elif code.op == 'add' and code.args[1] == 0:
                self.logger.info('Remove: add R, 0')
                return True
            elif code.op == 'sub' and code.args[1] == 0:
                self.logger.info('Remove: sub R, 0')
                return True
            elif code.op == 'imul' and code.args[1] == 1:
                self.logger.info('Remove: imul R, 1')
                return True
        return False

    def _optimize_single(self, code):
        """1行単位で行える最適化"""

        # 不要な行を削除
        new_code = []
        for line in code:
            if isinstance(line, Code) and self._check_single_deletable(line):
                self.optimized += 1
                continue
            new_code.append(line)
        return new_code

    def _optimize_save_and_load(self, code):
        """メモリストア直後のロード命令の削除"""
        store = None
        store_line = -1
        delete_lines = []

        for i, line in enumerate(code):
            if isinstance(line, Comment):
                continue
            elif isinstance(line, Code):
                if line.op == 'mov':
                    if (isinstance(line.args[0], (Data, Memory,))
                            and isinstance(line.args[1], Register)
                            and line.args[1] == Registers.eax):
                        # ストア
                        store = line.args[0]
                        store_line = i
                    elif (isinstance(line.args[1], (Data, Memory,))
                            and store is not None
                            and isinstance(line.args[0], Register)
                            and line.args[0] == Registers.eax
                            and store == line.args[1]):
                        # ロード
                        self.optimized += 1
                        delete_lines += [store_line, i]
                        store = None
                        self.logger.info(
                            'Remove: mov (load) after mov (store)')
                    else:
                        store = None
            else:
                store = None

        return [i for j, i in enumerate(code) if j not in delete_lines]

    def _is_register_read(self, code, register=Registers.eax):
        op = code.op.replace(' dword', '')

        # eax の場合の例外
        if register == Registers.eax:
            if op == 'movzx':
                if (isinstance(code.args[1], Registers)
                        and code.args[1] == Registers.al):
                    return True

        if op in ('cdq', 'idiv', 'ret',):
            return True
        elif op in ('add', 'and', 'cmp', 'dec', 'imul', 'inc', 'neg', 'or',
                'sub', 'test', 'xor',):
            for arg in code.args:
                if isinstance(arg, Registers) and arg == register:
                    return True
        elif op in ('mov', 'movzx',):
            if (isinstance(code.args[1], Registers)
                    and code.args[1] == register):
                return True

        return False

    def _is_register_write(self, code, register=Registers.eax):
        op = code.op.replace(' dword', '')

        if register == Registers.eax:
            # cdq, idiv は eax に結果を書き込む
            if op in ('cdq', 'idiv',):
                return True
            elif op in ('sete', 'setg', 'setge', 'setl', 'setle', 'setne',):
                if (isinstance(code.args[0], Registers)
                        and code.args[0] == Registers.al):
                    return True

        if op in ('add', 'and', 'call', 'dec', 'imul', 'inc', 'neg', 'mov',
                'movzx', 'or', 'pop', 'sub', 'xor',):
            if (isinstance(code.args[0], Registers)
                    and code.args[0] == register):
                return True

        return False

    def _optimize_unused_code(self, code):
        used = False
        start = -1
        delete_lines = []

        # 使用されないレジスタ書き込みを検出して削除する
        for i, line in enumerate(code):
            if isinstance(line, Label):
                start = -1
            elif isinstance(line, Code):
                if self._is_register_read(line):
                    start = -1
                elif self._is_register_write(line):
                    if start > 0:
                        self.optimized += 1
                        delete_lines.append(start)
                        start = -1
                        self.logger.info('Remove: unused mov (store)')
                    start = i

        return [i for j, i in enumerate(code) if j not in delete_lines]

    def optimize(self, code):
        code = self._optimize_single(code)
        code = self._optimize_save_and_load(code)
        code = self._optimize_unused_code(code)
        return code


class ReplaceCodeOptimizer(Optimizer):
    """より効率の良いコードに書き換えることによる最適化"""
    def optimize(self, code):
        for i, line in enumerate(code[:]):
            if isinstance(line, Code):
                if (line.op == 'mov'
                        and isinstance(line.args[0], Registers)
                        and isinstance(line.args[1], (int, str,))
                        and int(line.args[1]) == 0):
                    # mov を xor に置換する
                    code[i].op = 'xor'
                    code[i].args[1] = code[i].args[0]
                    code[i].comment += ' (Optimized mov -> xor)'
                    self.optimized += 1
                    self.logger.info('Replace: mov R, 0 -> xor R, R')
                elif (line.op == 'imul'
                        and isinstance(line.args[1], (int, str,))
                        and int(line.args[1]) == 0):
                    # 0 乗算 を mov に置換する
                    code[i].op = 'mov'
                    code[i].args[1] = 0
                    code[i].comment += ' (Optimized imul -> mov)'
                    self.optimized += 1
                    self.logger.info('Replace: imul R, 0 -> mov R, 0')
                elif line.op == 'inc':
                    # inc -> add
                    code[i].op = 'add'
                    code[i].args.append(1)
                    code[i].comment += ' (Optimized inc -> add)'
                    self.optimized += 1
                    self.logger.info('Replace: inc R -> add R, 1')
                elif line.op == 'dec':
                    # dec -> sub
                    code[i].op = 'sub'
                    code[i].args.append(1)
                    code[i].comment += ' (Optimized dec -> sub)'
                    self.optimized += 1
                    self.logger.info('Replace: dec R -> sub R, 1')
        return code


class StackPointerOptimzier(Optimizer):
    def optimize(self, code):
        flag = False
        functions = []
        start = -1
        end = -1
        offset = 0

        for i, line in enumerate(code):
            # 関数の開始地点を見つける
            if not isinstance(line, Code):
                continue
            elif (line.op == 'push'
                    and isinstance(line.args[0], Registers)
                    and line.args[0] == Registers.ebp):
                flag = True
                start = i
            elif start == i - 1:
                if not (line.op == 'mov'
                        and line.args[0] == Registers.ebp
                        and line.args[1] == Registers.esp):
                    flag = False
            elif start == i - 2:
                if line.op == 'sub' and line.args[0] == Registers.esp:
                    offset = int(line.args[1])
                else:
                    offset = 0
            # 関数中に Push があれば不成立
            elif flag and line.op == 'push':
                flag = False
            # 関数の終了地点を見つける
            elif flag and line.op == 'pop' and line.args[0] == Registers.ebp:
                end = i
                functions.append((start, offset, end,))

        for function in functions:
            for i, line in enumerate(code[function[0]:function[2] + 1]):
                if not isinstance(line, Code):
                    continue
                for j, memory in enumerate(line.args):
                    if (isinstance(memory, Memory)
                            and memory.register == Registers.ebp):
                        # ebp 相対アクセスを esp 相対アクセスに書き換え
                        code[function[0] + i].args[j].register = Registers.esp
                        offset = function[1] + memory.offset - 4
                        code[function[0] + i].args[j].offset = offset

                        self.logger.info('Replace: [ebp+n] -> [esp+n]')

        delete_lines = []
        for function in functions:
            self.optimized += 1
            self.logger.info('Remove: unnecessary calling conventions')

            # 関数の先頭と末尾の不要になった部分を削除
            delete_lines += [function[0], function[0] + 1, function[2] - 1]

            # 関数の最終行に esp を戻す処理を追加
            # (offset 0 のときも最適化されるので問題ない)
            code[function[2]] = Code('add', 'esp', function[1],
                                     comment='Optimized ebp -> esp')

        return [i for j, i in enumerate(code) if j not in delete_lines]
