from __future__ import annotations

from compiler_ast import (
    VariableDeclaration,
    Assignment,
    ExpressionStatement,
    TypeName,
    PrintStatement,
)

from tokens import TokenType


class StatementParserMixin:
    """
    Parses statements:

        int x = 5;
        var y = x + 1;
        x = 10;
        expression;
    """


    # ========================================================
    # Statement dispatcher
    # ========================================================

    def parse_statement(self):

        # variable declarations
        if self.check_type_start():

            return self.parse_variable_declaration()


        # assignment
        if self.check(TokenType.IDENTIFIER):

            if self.peek().type == TokenType.ASSIGN:

                return self.parse_assignment()


        # print statements
        if self.check(TokenType.PRINT):

            return self.parse_print_statement()


        # fallback: expression statement
        return self.parse_expression_statement()


    # ========================================================
    # Type detection
    # ========================================================

    def check_type_start(self):

        return self.current.type in (
            TokenType.TYPE_INT,
            TokenType.TYPE_FLOAT,
            TokenType.TYPE_STRING,
            TokenType.TYPE_BOOL,
            TokenType.VAR,
        )



    # ========================================================
    # Variable declaration
    # ========================================================

    def parse_variable_declaration(self):

        type_token = None

        declared_type = None


        # -------------------------
        # var x = expression;
        # -------------------------

        if self.match(TokenType.VAR):

            type_token = self.tokens[self.position - 1]

            declared_type = None


        else:

            # ---------------------
            # int x
            # ---------------------

            type_token = self.current

            self.advance()


            nullable = False


            if self.match(TokenType.QUESTION):

                nullable = True


            declared_type = TypeName(
                line=type_token.line,
                column=type_token.column,
                name=type_token,
                nullable=nullable,
            )


        # identifier

        identifier = self.consume_identifier()


        self.expect(
            TokenType.ASSIGN,
            "Expected '=' after variable name"
        )


        initializer = self.parse_expression()


        self.expect(
            TokenType.SEMICOLON,
            "Expected ';' after variable declaration"
        )


        return VariableDeclaration(

            line=identifier.line,
            column=identifier.column,

            identifier=identifier,

            declared_type=declared_type,

            initializer=initializer,
        )



    # ========================================================
    # Assignment
    # ========================================================

    def parse_assignment(self):

        identifier = self.consume_identifier()


        self.expect(
            TokenType.ASSIGN,
            "Expected '=' after identifier"
        )


        value = self.parse_expression()


        self.expect(
            TokenType.SEMICOLON,
            "Expected ';' after assignment"
        )


        return Assignment(

            line=identifier.line,
            column=identifier.column,

            identifier=identifier,

            value=value,
        )



    # ========================================================
    # Expression statement
    # ========================================================

    def parse_expression_statement(self):

        expression = self.parse_expression()


        self.expect(
            TokenType.SEMICOLON,
            "Expected ';' after expression"
        )


        return ExpressionStatement(

            line=expression.line,
            column=expression.column,

            expression=expression,
        )
        
    
    # ========================================================
    # Print statement
    # ========================================================
    
    def parse_print_statement(self):

        token = self.expect(TokenType.PRINT)

        self.expect(
            TokenType.LPAREN,
            "Expected '(' after print"
        )

        expression = self.parse_expression()

        self.expect(
            TokenType.RPAREN,
            "Expected ')' after expression"
        )

        self.expect(
            TokenType.SEMICOLON,
            "Expected ';'"
        )

        return PrintStatement(
            line=token.line,
            column=token.column,
            expression=expression
        )