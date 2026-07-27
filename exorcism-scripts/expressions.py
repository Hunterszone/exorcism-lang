from __future__ import annotations

from compiler_ast import (
    BinaryExpression,
    UnaryExpression,
    VariableReference,
    IntegerLiteral,
    FloatLiteral,
    StringLiteral,
    BooleanLiteral,
    NullLiteral,
    FunctionCall,
)

from tokens import TokenType


class ExpressionParserMixin:
    """
    Expression parsing using recursive descent
    with precedence levels.
    """


    # ========================================================
    # Entry point
    # ========================================================

    def parse_expression(self):

        return self.parse_or()


    # ========================================================
    # Logical OR
    # ========================================================

    def parse_or(self):

        expr = self.parse_and()

        while self.match(TokenType.OR):

            operator = self.tokens[self.position - 1]

            right = self.parse_and()

            expr = BinaryExpression(
                line=operator.line,
                column=operator.column,
                left=expr,
                operator=operator,
                right=right,
            )

        return expr


    # ========================================================
    # Logical AND
    # ========================================================

    def parse_and(self):

        expr = self.parse_equality()

        while self.match(TokenType.AND):

            operator = self.tokens[self.position - 1]

            right = self.parse_equality()

            expr = BinaryExpression(
                line=operator.line,
                column=operator.column,
                left=expr,
                operator=operator,
                right=right,
            )

        return expr


    # ========================================================
    # Equality
    # ========================================================

    def parse_equality(self):

        expr = self.parse_comparison()

        while self.match(
            TokenType.EQUAL,
            TokenType.NOT_EQUAL
        ):

            operator = self.tokens[self.position - 1]

            right = self.parse_comparison()

            expr = BinaryExpression(
                line=operator.line,
                column=operator.column,
                left=expr,
                operator=operator,
                right=right,
            )

        return expr


    # ========================================================
    # Comparison
    # ========================================================

    def parse_comparison(self):

        expr = self.parse_term()

        while self.match(
            TokenType.LESS,
            TokenType.LESS_EQUAL,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
        ):

            operator = self.tokens[self.position - 1]

            right = self.parse_term()

            expr = BinaryExpression(
                line=operator.line,
                column=operator.column,
                left=expr,
                operator=operator,
                right=right,
            )

        return expr


    # ========================================================
    # Addition / subtraction
    # ========================================================

    def parse_term(self):

        expr = self.parse_factor()

        while self.match(
            TokenType.PLUS,
            TokenType.MINUS,
        ):

            operator = self.tokens[self.position - 1]

            right = self.parse_factor()

            expr = BinaryExpression(
                line=operator.line,
                column=operator.column,
                left=expr,
                operator=operator,
                right=right,
            )

        return expr


    # ========================================================
    # Multiplication / division
    # ========================================================

    def parse_factor(self):

        expr = self.parse_unary()

        while self.match(
            TokenType.STAR,
            TokenType.SLASH,
        ):

            operator = self.tokens[self.position - 1]

            right = self.parse_unary()

            expr = BinaryExpression(
                line=operator.line,
                column=operator.column,
                left=expr,
                operator=operator,
                right=right,
            )

        return expr


    # ========================================================
    # Unary operators
    # ========================================================

    def parse_unary(self):

        if self.match(
            TokenType.NOT,
            TokenType.MINUS,
        ):

            operator = self.tokens[self.position - 1]

            operand = self.parse_unary()

            return UnaryExpression(
                line=operator.line,
                column=operator.column,
                operator=operator,
                operand=operand,
            )


        return self.parse_primary()


    # ========================================================
    # Primary expressions
    # ========================================================

    def parse_primary(self):
        
        token = self.current

        # integer

        if self.match(TokenType.INTEGER):

            return IntegerLiteral(
                line=token.line,
                column=token.column,
                value=token.value,
            )


        # float

        if self.match(TokenType.FLOAT):

            return FloatLiteral(
                line=token.line,
                column=token.column,
                value=token.value,
            )


        # string

        if self.match(TokenType.STRING):

            return StringLiteral(
                line=token.line,
                column=token.column,
                value=token.value,
            )


        # boolean true

        if self.match(TokenType.TRUE):

            return BooleanLiteral(
                line=token.line,
                column=token.column,
                value=True,
            )


        # boolean false

        if self.match(TokenType.FALSE):

            return BooleanLiteral(
                line=token.line,
                column=token.column,
                value=False,
            )


        # null

        if self.match(TokenType.NULL):

            return NullLiteral(
                line=token.line,
                column=token.column,
            )


        # identifier / function call

        if self.check(TokenType.IDENTIFIER):

            token = self.advance()


            # function call: name(...)
            if self.match(TokenType.LPAREN):

                arguments = []


                if not self.check(TokenType.RPAREN):

                    arguments.append(
                        self.parse_expression()
                    )


                    while self.match(TokenType.COMMA):

                        arguments.append(
                            self.parse_expression()
                        )


                self.expect(
                    TokenType.RPAREN,
                    "Expected ')' after arguments"
                )


                return FunctionCall(

                    line=token.line,

                    column=token.column,

                    name=token.value,

                    arguments=arguments
                )


            # normal variable: name

            return VariableReference(

                line=token.line,

                column=token.column,

                identifier=token,
            )


        # parenthesized expression

        if self.match(TokenType.LPAREN):

            expr = self.parse_expression()

            self.expect(
                TokenType.RPAREN,
                "Expected ')' after expression"
            )

            return expr
            
            
        self.error(
            "Expected expression",
            self.current
        )