from __future__ import annotations

from compiler_ast import Program

from tokens import TokenType

from base import ParserBase
from expressions import ExpressionParserMixin
from statements import StatementParserMixin
from controlflow import ControlFlowParserMixin



class Parser(
    ParserBase,
    ExpressionParserMixin,
    StatementParserMixin,
    ControlFlowParserMixin,
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


        # normal statement

        return self.parse_statement()