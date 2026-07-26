from __future__ import annotations

from compiler_ast import Program, FunctionCall

from tokens import TokenType

from base import ParserBase
from expressions import ExpressionParserMixin
from statements import StatementParserMixin
from controlflow import ControlFlowParserMixin
from functions import FunctionParserMixin


class Parser(
    ParserBase,
    ExpressionParserMixin,
    StatementParserMixin,
    ControlFlowParserMixin,
    FunctionParserMixin,
):
    """
    Complete language parser.

    Combines:

        ParserBase
            |
            +-- expressions
            |
            +-- statements
            |
            +-- control flow

    Produces:

        Program AST
    """


    def __init__(self, tokens):

        super().__init__(tokens)



    # ========================================================
    # Main entry point
    # ========================================================

    def parse(self):

        statements = []


        while not self.is_at_end():


            try:

                statement = self.parse_top_level_statement()

                statements.append(statement)


            except Exception:

                self.synchronize()

                raise



        return Program(

            line=1,

            column=1,

            statements=statements,
        )



    # ========================================================
    # Top-level statement dispatcher
    # ========================================================

    def parse_top_level_statement(self):


        # if statement

        if self.check(TokenType.IF):

            return self.parse_if_statement()


        # function declaration

        if self.is_function_declaration():

            return self.parse_function_declaration(
                self.parse_type()
            )


        # normal statement

        return self.parse_statement()
        
        
    # ========================================================
    # Helpers
    # ========================================================
    
    def is_function_declaration(self):

        saved = self.save()

        try:

            if not self.check_type_start():
                return False

            self.parse_type()

            return (
                self.check(TokenType.IDENTIFIER)
                and self.peek().type == TokenType.LPAREN
            )

        finally:

            self.restore(saved)
            
    
    def parse_type(self):

        if self.check(TokenType.TYPE_INT):

            token = self.advance()

            return token.value


        if self.check(TokenType.TYPE_FLOAT):

            token = self.advance()

            return token.value


        if self.check(TokenType.TYPE_STRING):

            token = self.advance()

            return token.value
            
            
        if self.check(TokenType.TYPE_BOOL):

            token = self.advance()

            return token.value


        raise ParserError(
            "Expected type"
        )