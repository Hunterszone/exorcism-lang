from __future__ import annotations

from compiler_ast import (
    Block,
    IfStatement,
)


from tokens import TokenType


class ControlFlowParserMixin:
    """
    Parses:

        if (condition)
        {
            statements
        }
        else
        {
            statements
        }

    and:

        {
            statements
        }
    """


    # ========================================================
    # Block parsing
    # ========================================================

    def parse_block(self):
        """Parse a braced block and return its statements."""

        opening = self.expect(
            TokenType.LBRACE,
            "Expected '{'"
        )

        statements = []


        while (
            not self.check(TokenType.RBRACE)
            and not self.is_at_end()
        ):

            statements.append(
                self.parse_statement()
            )


        self.expect(
            TokenType.RBRACE,
            "Expected '}' after block"
        )


        return Block(

            line=opening.line,
            column=opening.column,

            statements=statements,
        )


    # ========================================================
    # If / Else
    # ========================================================

    def parse_if_statement(self):
        """Parse an if/option/else conditional chain."""

        if_token = self.expect(
            TokenType.IF
        )


        # ---------------------------------
        # IF condition
        # ---------------------------------

        self.expect(
            TokenType.LPAREN,
            "Expected '(' after if"
        )


        condition = self.parse_expression()


        self.expect(
            TokenType.RPAREN,
            "Expected ')' after condition"
        )


        # ---------------------------------
        # IF block
        # ---------------------------------

        then_block = self.parse_block()


        # ---------------------------------
        # OPTION branches
        # ---------------------------------

        alternatives = []


        while self.match(TokenType.OPTION):

            self.expect(
                TokenType.LPAREN,
                "Expected '(' after option"
            )


            option_condition = (
                self.parse_expression()
            )


            self.expect(
                TokenType.RPAREN,
                "Expected ')' after option condition"
            )


            option_block = self.parse_block()


            alternatives.append(
                (
                    option_condition,
                    option_block
                )
            )


        # ---------------------------------
        # ELSE
        # ---------------------------------

        else_block = None


        if self.match(TokenType.ELSE):

            else_block = self.parse_block()


        # ---------------------------------
        # AST
        # ---------------------------------

        return IfStatement(

            line=if_token.line,

            column=if_token.column,

            condition=condition,

            then_block=then_block,

            alternatives=alternatives,

            else_block=else_block,
        )