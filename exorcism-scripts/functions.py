from compiler_ast import (
    FunctionDeclaration,
    Parameter,
    FunctionCall,
    ReturnStatement,
)


class FunctionParserMixin:


    # ============================================================
    # Function declaration
    # ============================================================

    def parse_function_declaration(
        self,
        return_type
    ):

        name_token = self.consume(
            TokenType.IDENTIFIER,
            "Expected function name"
        )

        self.consume(
            TokenType.LPAREN,
            "Expected '(' after function name"
        )


        parameters = self.parse_parameters()


        self.consume(
            TokenType.RPAREN,
            "Expected ')' after parameters"
        )


        self.consume(
            TokenType.LBRACE,
            "Expected '{' before function body"
        )


        body = []


        while not self.check(TokenType.RBRACE):

            body.append(
                self.parse_statement()
            )


        self.consume(
            TokenType.RBRACE,
            "Expected '}' after function body"
        )


        return FunctionDeclaration(

            return_type=return_type,

            name=name_token.value,

            parameters=parameters,

            body=body
        )



    # ============================================================
    # Parameters
    # ============================================================

    def parse_parameters(self):

        parameters = []


        if self.check(TokenType.RPAREN):

            return parameters


        while True:


            parameter_type = (
                self.parse_type()
            )


            name = self.consume(
                TokenType.IDENTIFIER,
                "Expected parameter name"
            )


            parameters.append(

                Parameter(

                    parameter_type=
                        parameter_type,

                    name=
                        name.value
                )
            )


            if not self.match(
                TokenType.COMMA
            ):

                break


        return parameters



    # ============================================================
    # Function call
    # ============================================================

    def parse_function_call(
        self,
        name
    ):

        self.consume(
            TokenType.LPAREN,
            "Expected '('"
        )


        arguments = []


        if not self.check(
            TokenType.RPAREN
        ):

            while True:

                arguments.append(
                    self.parse_expression()
                )


                if not self.match(
                    TokenType.COMMA
                ):

                    break


        self.consume(
            TokenType.RPAREN,
            "Expected ')'"
        )


        return FunctionCall(

            name=name,

            arguments=arguments
        )



    # ============================================================
    # Return statement
    # ============================================================

    def parse_return_statement(self):

        self.consume(
            TokenType.RETURN,
            "Expected return"
        )


        expression = None


        if not self.check(
            TokenType.SEMICOLON
        ):

            expression = (
                self.parse_expression()
            )


        self.consume(
            TokenType.SEMICOLON,
            "Expected ';'"
        )


        return ReturnStatement(
            expression=expression
        )