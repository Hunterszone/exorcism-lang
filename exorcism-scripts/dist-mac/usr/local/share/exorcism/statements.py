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
        """Parse and return the next statement."""

        parser = self.parse_expression_statement

        # variable declaration
        if self.check(TokenType.VAR):

            parser = self.parse_variable_declaration

        # typed variable declarations
        elif self.check_type_start():

            parser = self.parse_variable_declaration

        # if statements    
        elif self.check(TokenType.IF):

            parser = self.parse_if_statement

        # print statements
        elif self.check(TokenType.PRINT):

            parser = self.parse_print_statement

        # return statements
        elif self.check(TokenType.RETURN):

            parser = self.parse_return_statement

        # assignment
        elif (self.check(TokenType.IDENTIFIER)
              and self.peek().type == TokenType.ASSIGN):

            parser = self.parse_assignment

        return parser()


    # ========================================================
    # Type detection
    # ========================================================

    def check_type_start(self):
        """Return whether the current token starts a type declaration."""

        return self.current.type in (
            TokenType.TYPE_INT,
            TokenType.TYPE_FLOAT,
            TokenType.TYPE_DOUBLE,
            TokenType.TYPE_CHAR,
            TokenType.TYPE_STRING,
            TokenType.TYPE_BOOL,
            TokenType.TYPE_VOID,
        )


    # ========================================================
    # Variable declaration
    # ========================================================

    def parse_variable_declaration(self):
        """Parse a variable declaration statement."""

        declared_type = None


        # ---------------------------------
        # var x = expression;
        # ---------------------------------

        if self.match(TokenType.VAR):

            declared_type = None


        else:

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


        # ---------------------------------
        # identifier
        # ---------------------------------

        identifier = self.consume_identifier()


        self.expect(
            TokenType.ASSIGN,
            "Expected '=' after variable name"
        )


        # ---------------------------------
        # initializer
        # ---------------------------------

        initializer = self.parse_expression()


        self.expect(
            TokenType.SEMICOLON,
            "Expected ';' after variable declaration",
            error_token=self.previous
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
        """Parse an assignment statement."""

        identifier = self.consume_identifier()


        self.expect(
            TokenType.ASSIGN,
            "Expected '=' after identifier"
        )


        value = self.parse_expression()


        self.expect(
            TokenType.SEMICOLON,
            "Expected ';' after assignment",
            error_token=self.previous
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
        """Parse an expression statement terminated by a semicolon."""

        expression = self.parse_expression()


        self.expect(
            TokenType.SEMICOLON,
            "Expected ';' after expression",
            error_token=self.previous
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
        """Parse a print statement terminated by a semicolon."""

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
            "Expected ';'",
            error_token=self.previous
        )

        return PrintStatement(
            line=token.line,
            column=token.column,
            expression=expression
        )