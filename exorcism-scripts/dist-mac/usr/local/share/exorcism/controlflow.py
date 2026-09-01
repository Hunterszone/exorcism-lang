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

        closing = self.expect(
            TokenType.RBRACE,
            "Expected '}' after block"
        )

        return Block(
            line=opening.line,
            column=opening.column,
            statements=statements,
            end_token=closing,
        )


    # ========================================================
    # If / Else
    # ========================================================

    def parse_if_statement(self):
        """Parse an if/alt/else conditional chain."""

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
        # ALT branches
        # ---------------------------------

        alternatives = []


        while self.match(TokenType.ALT):

            self.expect(
                TokenType.LPAREN,
                "Expected '(' after alt"
            )


            alt_condition = (
                self.parse_expression()
            )


            self.expect(
                TokenType.RPAREN,
                "Expected ')' after alt condition"
            )


            alt_block = self.parse_block()


            alternatives.append(
                (
                    alt_condition,
                    alt_block
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