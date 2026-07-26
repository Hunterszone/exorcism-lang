from compiler_ast import (
    FunctionDeclaration,
    Parameter,
    FunctionCall,
    ReturnStatement,
)

from tokens import TokenType

class FunctionParserMixin:


    # ============================================================
    # Function declaration
    # ============================================================

    def parse_function_declaration(
        self,
        return_type
    ):

        token = self.current
        
        name_token = self.consume_identifier()

        self.expect(
            TokenType.LPAREN,
            "Expected '(' after function name"
        )


        parameters = self.parse_parameters()


        self.expect(
            TokenType.RPAREN,
            "Expected ')' after parameters"
        )


        self.expect(
            TokenType.LBRACE,
            "Expected '{' before function body"
        )


        body = []


        while not self.check(TokenType.RBRACE):

            body.append(
                self.parse_statement()
            )


        self.expect(
            TokenType.RBRACE,
            "Expected '}' after function body"
        )


        return FunctionDeclaration(
        
            line=token.line,

            column=token.column,

            return_type=return_type,

            name=name_token.value,

            parameters=parameters,

            body=body,
            
            token=name_token
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


            name = self.expect(
                TokenType.IDENTIFIER,
                "Expected parameter name"
            )


            parameters.append(

                Parameter(
                
                    line=name.line,

                    column=name.column,

                    parameter_type=
                        parameter_type,

                    name=
                        name.value
                        
                    # token=name
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

        self.expect(
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


        self.expect(
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
        
        token = self.current

        self.expect(
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


        self.expect(
            TokenType.SEMICOLON,
            "Expected ';'"
        )


        return ReturnStatement(
        
            line=token.line,

            column=token.column,
            
            expression=expression
        )