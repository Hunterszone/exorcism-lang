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
        """Parse an if statement, including optional else branches."""

        if_token = self.expect(
            TokenType.IF
        )


        self.expect(
            TokenType.LPAREN,
            "Expected '(' after if"
        )


        condition = self.parse_expression()


        self.expect(
            TokenType.RPAREN,
            "Expected ')' after condition"
        )


        then_block = self.parse_block()


        else_block = None


        if self.match(TokenType.ELSE):
            
            if self.check(TokenType.IF):

                nested_if = self.parse_if_statement()

                else_block = Block(
                    line=nested_if.line,
                    column=nested_if.column,
                    statements=[
                        nested_if
                    ],
                )

            else:

                else_block = self.parse_block()



        return IfStatement(

            line=if_token.line,
            column=if_token.column,

            condition=condition,

            then_block=then_block,

            else_block=else_block,
        )