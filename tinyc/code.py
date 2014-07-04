#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import enum


class Code(object):
    def __init__(self, op, *args, **kwargs):
        self.op = op
        self.args = list(args)
        self.comment = kwargs.get('comment', None)

    def __str__(self):
        # dword が必要か判定
        dword = True
        if len(self.args) == 0:
            dword = False
        for arg in self.args:
            if isinstance(arg, Label):
                dword = False
                break
            elif isinstance(arg, Registers):
                dword = False
                break
            elif isinstance(arg, (str, unicode,)):
                if arg in ('al', 'eax', 'ebp', 'esp',):
                    dword = False
                    break

        # 必要であれば dword を付加
        op = self.op
        if dword:
            op += ' dword'

        # 引数を文字列のリストに変換
        args = []
        for arg in self.args:
            if isinstance(arg, Registers):
                args.append(arg.value)
            else:
                args.append(arg)
        args = ', '.join(map(str, args))

        if self.comment is None:
            return " " * 4 + "{0:11} {1:16}".format(op, args).strip()
        else:
            return " " * 4 + "{0:11} {1:15} ; {2}".format(
                op, args, self.comment).strip()


class Common(object):
    def __init__(self, label, byte=4):
        self.label = label
        self.bytes = byte

    def __str__(self):
        return "    COMMON      {0} {1}".format(self.label, self.bytes)


class Comment(object):
    def __init__(self, comment):
        self.comment = comment

    def __str__(self):
        return '; ' + self.comment


class Data(object):
    def __init__(self, label):
        self.label = label

    def __str__(self):
        return '[{0}]'.format(self.label)


class Extern(object):
    def __init__(self, label):
        self.label = label

    def __eq__(self, other):
        return self.label == other.label

    def __ne__(self, other):
        return self.label != other.label

    def __str__(self):
        return "    EXTERN      " + str(self.label)


class Global(object):
    def __init__(self, label):
        self.label = label

    def __eq__(self, other):
        return self.label == other.label

    def __ne__(self, other):
        return self.label != other.label

    def __str__(self):
        return "    GLOBAL      " + str(self.label)


class Label(object):
    def __init__(self, label, **kwargs):
        self.label = label

    def __eq__(self, other):
        return self.label == other.label

    def __ne__(self, other):
        return self.label != other.label

    def __str__(self):
        return self.label


class Memory(object):
    def __init__(self, register, offset):
        self.register = register
        self.offset = offset

    def __eq__(self, other):
        return (self.register == other.register
                and self.offset == other.offset)

    def __str__(self):
        return '[{0}{1:+d}]'.format(self.register.value, self.offset)


class Register(object):
    def __init__(self, register):
        self.register = register

    def __eq__(self, other):
        return self.register == other.register

    def __str__(self):
        return self.register


class Registers(enum.Enum):
    al = Register('al')
    eax = Register('eax')
    ebp = Register('ebp')
    esp = Register('esp')


class Section(object):
    def __init__(self, tp):
        self.tp = tp

    def __str__(self):
        return 'section .' + self.tp
