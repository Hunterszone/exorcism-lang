from __future__ import annotations

from tokens import Token, TokenType


class ParserError(Exception):
    """Error raised when parsing fails."""

    def __init__(
        self,
        message,
        token=None,
        related_token=None
    ):

        super().__init__(message)

        self.message = message
        self.token = token
        self.related_token = related_token


class ParserBase:
    """
    Core parser functionality.

    Other parser modules inherit from this class:
        - expressions.py
        - statements.py
        - controlflow.py
        - parser.py
    """

    def __init__(self, tokens: list[Token]):

        self.tokens = tokens
        self.position = 0

        self.current = tokens[0]


    # ========================================================
    # Token navigation
    # ========================================================

    def advance(self) -> Token:
        """
        Move to the next token.

        Returns the consumed token.
        """

        previous = self.current

        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current = self.tokens[self.position]

        return previous


    @property
    def previous(self) -> Token:
        """Return the previously consumed token."""

        if self.position == 0:
            return self.tokens[0]

        return self.tokens[self.position - 1]
    
    
    def peek(self, offset: int = 1) -> Token:
        """
        Look ahead without consuming.
        """

        index = self.position + offset

        if index >= len(self.tokens):
            return self.tokens[-1]

        return self.tokens[index]


    # ========================================================
    # Matching helpers
    # ========================================================

    def check(self, token_type: TokenType) -> bool:
        """
        Check current token type.
        """

        return self.current.type == token_type


    def match(self, *token_types: TokenType) -> bool:
        """
        If current token matches one of the types,
        consume it and return True.
        """

        for token_type in token_types:

            if self.check(token_type):
                self.advance()
                return True

        return False


    def expect(
        self,
        token_type: TokenType,
        message: str | None = None,
        error_token: Token | None = None
    ) -> Token:
        """Consume the current token if it matches the expected type."""

        if self.check(token_type):
            return self.advance()

        token = (
            error_token
            if error_token is not None
            else self.current
        )

        if message is None:

            message = (
                f"Expected {token_type.name}, "
                f"got {self.current.type.name}"
            )


        raise ParserError(
            message,
            token=token
        )

    # ========================================================
    # State helpers
    # ========================================================

    def is_at_end(self) -> bool:
        """Return whether the current token is the end-of-file marker."""

        return self.current.type == TokenType.EOF


    def consume_identifier(self) -> Token:
        """
        Consume an identifier token.
        """

        return self.expect(
            TokenType.IDENTIFIER,
            "Expected identifier"
        )


    # ========================================================
    # Diagnostics
    # ========================================================

    def error(
        self,
        message: str,
        token: Token | None = None
    ):
        """Raise a parser error for the specified message and token."""

        if token is None:
            token = self.current

        raise ParserError(
            message,
            token=token
        )

    
    def save(self):
        """Return the current parser position for later restoration."""

        return self.position


    def restore(self, position):
    
        self.position = position
        self.current = self.tokens[position]


    def synchronize(self):
        """
        Basic error recovery.

        Used later so the parser can continue
        after a syntax error and report more
        than one problem.
        """

        while not self.is_at_end():

            if self.current.type == TokenType.SEMICOLON:
                self.advance()
                return

            if self.current.type in (
                TokenType.IF,
                TokenType.ELSE,
                TokenType.LBRACE,
                TokenType.RBRACE,
            ):
                return

            self.advance()