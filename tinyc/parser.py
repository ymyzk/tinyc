#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys

from ply import yacc

from tinyc import common, token
from tinyc.common import Kinds
from tinyc.lexer import Lexer


class Parser(object):
    u"""構文解析器"""
    tokens = common.TOKENS

    def p_program_external_declaration(self, p):
        """program : external_declaration"""
        p[0] = token.ExternalDeclarationList(p[1])

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
        p[0] = token.Declaration(p[2])

    def p_declarator_list_declarator(self, p):
        """declarator_list : declarator"""
        p[0] = token.DeclaratorList(p[1])

    def p_declarator_list_declarator_list(self, p):
        """declarator_list : declarator COMMA declarator_list"""
        p[3].insert(0, p[1])
        p[0] = p[3]

    def p_declarator(self, p):
        """declarator : identifier"""
        p[0] = token.Declarator(p[1])

    def p_function_definition(self, p):
        """function_definition : INT declarator LPAREN parameter_type_list_opt RPAREN compound_statement"""
        p[0] = token.FunctionDefinition(p[2], p[4], p[6])

    def p_parameter_type_list_opt(self, p):
        """parameter_type_list_opt : empty
                                   | parameter_type_list"""
        if isinstance(p[1], token.NullNode):
            p[1] = token.ParameterTypeList()
        p[0] = p[1]

    def p_parameter_type_list_parameter_declaration(self, p):
        """parameter_type_list : parameter_declaration"""
        p[0] = token.ParameterTypeList(p[1])

    def p_parameter_type_list_parameter_type_list(self, p):
        """parameter_type_list : parameter_type_list COMMA parameter_declaration"""
        p[1].add(p[3])
        p[0] = p[1]

    def p_parameter_declaration(self, p):
        """parameter_declaration : INT declarator"""
        p[0] = token.ParameterDeclaration(p[2])

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
        p[0] = token.IfStatement(p[3], p[5], token.NullNode())

    def p_statement_if_else(self, p):
        """statement : IF LPAREN expression RPAREN statement ELSE statement"""
        p[0] = token.IfStatement(p[3], p[5], p[7])

    def p_statement_while(self, p):
        """statement : WHILE LPAREN expression RPAREN statement"""
        p[0] = token.WhileLoop(p[3], p[5])

    def p_statement_return(self, p):
        """statement : RETURN expression SEMICOLON"""
        p[0] = token.ReturnStatement(p[2])

    def p_compound_statement_empty(self, p):
        """compound_statement : LBRACE RBRACE"""
        p[0] = token.CompoundStatement(token.NullNode(), token.NullNode())

    def p_compound_statement_declaration(self, p):
        """compound_statement : LBRACE declaration_list RBRACE"""
        p[0] = token.CompoundStatement(p[2], token.StatementList())

    def p_compound_statement_statement(self, p):
        """compound_statement : LBRACE statement_list RBRACE"""
        p[0] = token.CompoundStatement(token.DeclarationList(), p[2])

    def p_compound_statement_declaration_statement(self, p):
        """compound_statement : LBRACE declaration_list statement_list RBRACE"""
        p[0] = token.CompoundStatement(p[2], p[3])

    def p_declaration_list_declaration(self, p):
        """declaration_list : declaration"""
        p[0] = token.DeclarationList(p[1])

    def p_declaration_list_declaration_list(self, p):
        """declaration_list : declaration_list declaration"""
        p[1].add(p[2])
        p[0] = p[1]

    def p_statement_list_statement(self, p):
        """statement_list : statement"""
        p[0] = token.StatementList(p[1])

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
        p[0] = token.BinaryOperator('ASSIGN', p[1], p[3])

    def p_assign_expr_assign_plus(self, p):
        """assign_expr : identifier PLUS_EQ assign_expr"""
        p[0] = token.BinaryOperator('ASSIGN_PLUS', p[1], p[3])

    def p_assign_expr_assign_minus(self, p):
        """assign_expr : identifier MINUS_EQ assign_expr"""
        p[0] = token.BinaryOperator('ASSIGN_MINUS', p[1], p[3])

    def p_logical_OR_expr_and_expr(self, p):
        """logical_OR_expr : logical_AND_expr"""
        p[0] = p[1]

    def p_logical_OR_expr_or(self, p):
        """logical_OR_expr : logical_OR_expr LOR logical_AND_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] == token.Constant(1) or p[3] == token.Constant(1):
                p[0] = token.Constant(1)
            else:
                p[0] = token.Constant(0)
        else:
            p[0] = token.BinaryOperator('LOR', p[1], p[3])

    def p_logical_AND_expr_equality_expr(self, p):
        """logical_AND_expr : equality_expr"""
        p[0] = p[1]

    def p_logical_AND_expr_and(self, p):
        """logical_AND_expr : logical_AND_expr LAND equality_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] == token.Constant(1) and p[3] == token.Constant(1):
                p[0] = token.Constant(1)
            else:
                p[0] = token.Constant(0)
        else:
            p[0] = token.BinaryOperator('LAND', p[1], p[3])

    def p_equality_expr_relational_expr(self, p):
        """equality_expr : relational_expr"""
        p[0] = p[1]

    def p_equality_expr_eq(self, p):
        """equality_expr :  equality_expr EQ relational_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] == p[3]:
                p[0] = token.Constant(1)
            else:
                p[0] = token.Constant(0)
        else:
            p[0] = token.BinaryOperator('EQ', p[1], p[3])

    def p_equality_expr_neq(self, p):
        """equality_expr : equality_expr NEQ relational_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] != p[3]:
                p[0] = token.Constant(1)
            else:
                p[0] = token.Constant(0)
        else:
            p[0] = token.BinaryOperator('NEQ', p[1], p[3])

    def p_relational_expr_add(self, p):
        """relational_expr : add_expr"""
        p[0] = p[1]

    def p_relational_expr_lt(self, p):
        """relational_expr : relational_expr LT add_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] < p[3]:
                p[0] = token.Constant(1)
            else:
                p[0] = token.Constant(0)
        else:
            p[0] = token.BinaryOperator('LT', p[1], p[3])

    def p_relational_expr_lte(self, p):
        """relational_expr : relational_expr LTE add_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] <= p[3]:
                p[0] = token.Constant(1)
            else:
                p[0] = token.Constant(0)
        else:
            p[0] = token.BinaryOperator('LTE', p[1], p[3])

    def p_relational_expr_gt(self, p):
        """relational_expr : relational_expr GT add_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] > p[3]:
                p[0] = token.Constant(1)
            else:
                p[0] = token.Constant(0)
        else:
            p[0] = token.BinaryOperator('GT', p[1], p[3])

    def p_relational_expr_gte(self, p):
        """relational_expr : relational_expr GTE add_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            if p[1] >= p[3]:
                p[0] = token.Constant(1)
            else:
                p[0] = token.Constant(0)
        else:
            p[0] = token.BinaryOperator('GTE', p[1], p[3])

    def p_add_expr_mult_expr(self, p):
        """add_expr : mult_expr"""
        p[0] = p[1]

    def p_add_expr_plus(self, p):
        """add_expr : add_expr PLUS mult_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            p[0] = p[1] + p[3]
        else:
            p[0] = token.BinaryOperator('PLUS', p[1], p[3])

    def p_add_expr_minus(self, p):
        """add_expr : add_expr MINUS mult_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            p[0] = p[1] - p[3]
        else:
            p[0] = token.BinaryOperator('MINUS', p[1], p[3])

    def p_mult_expr_unary_expr(self, p):
        """mult_expr : unary_expr"""
        p[0] = p[1]

    def p_mult_expr_mult(self, p):
        """mult_expr : mult_expr MULT unary_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            p[0] = p[1] * p[3]
        else:
            p[0] = token.BinaryOperator('MULT', p[1], p[3])

    def p_mult_expr_div(self, p):
        """mult_expr : mult_expr DIV unary_expr"""
        if self.optimize and self._check_if_constants(p[1], p[3]):
            self.optimized += 1
            p[0] = p[1] / p[3]
        else:
            p[0] = token.BinaryOperator('DIV', p[1], p[3])

    def p_unary_expr_postfix(self, p):
        """unary_expr : postfix_expr"""
        p[0] = p[1]

    def p_unary_expr_minus(self, p):
        """unary_expr : MINUS unary_expr"""
        if self.optimize and self._check_if_constants(p[2]):
            self.optimized += 1
            p[0] = -p[2]
        else:
            p[0] = token.Negative(p[2])

    def p_unary_expr_increment(self, p):
        """unary_expr : INC identifier"""
        p[0] = token.Increment(p[2])

    def p_unary_expr_decrement(self, p):
        """unary_expr : DEC identifier"""
        p[0] = token.Decrement(p[2])

    def p_postfix_expr_primary_expr(self, p):
        """postfix_expr : primary_expr"""
        p[0] = p[1]

    def p_postfix_expr_fcall(self, p):
        """postfix_expr : identifier LPAREN argument_expression_list_opt RPAREN"""
        p[0] = token.FunctionExpression(p[1], p[3], p[1].lineno)

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
        if isinstance(p[1], token.NullNode):
            p[1] = token.ArgumentExpressionList()
        p[0] = p[1]

    def p_argument_expression_list_assign_expr(self, p):
        """argument_expression_list : assign_expr"""
        p[0] = token.ArgumentExpressionList(p[1])

    def p_argument_expression_list_argument_expression_list(self, p):
        """argument_expression_list : argument_expression_list COMMA assign_expr"""
        p[1].add(p[3])
        p[0] = p[1]

    def p_identifier(self, p):
        """identifier : ID"""
        p[0] = token.Identifier(p[1], p.lineno(1))

    def p_constant(self, p):
        """constant : CONSTANT"""
        p[0] = token.Constant(p[1])

    def p_empty(self, p):
        """empty : """
        p[0] = token.NullNode()

    def p_error(self, p):
        self.errors += 1
        message = "Line {line}: Syntax error at '{value}'. "
        print(
            message.format(
                line=p.lineno,
                value=p.value),
            file=sys.stderr)

        # Panic mode に突入, 特定のトークンまで読み飛ばす
        while True:
            token = yacc.token()
            if not token or token.type in ('SEMICOLON', 'RBRACE',):
                break
        # 構文解析を再開
        self.parser.restart()

    # else は右結合的に処理する
    precedence = (
        ('right', 'ELSE',),
    )

    def _check_if_constants(self, *args):
        for arg in args:
            if not isinstance(arg, token.Constant):
                return False
        return True

    def build(self, debug=False, **kwargs):
        self.errors = 0
        self.optimized = 0

        # 字句解析
        self.lexer = Lexer()
        self.lexer.build(debug=debug)
        self.parser = yacc.yacc(module=self, debug=debug)

    def parse(self, data, optimize=True):
        self.optimize = optimize
        result = self.parser.parse(data)
        self.errors += self.lexer.errors
        return result
