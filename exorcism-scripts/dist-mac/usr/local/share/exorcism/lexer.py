from tokens import Token, TokenType, KEYWORDS


class LexerError(Exception):
    """Exception raised for lexer errors."""

    def __init__(
        self,
        message,
        line,
        column
    ):

        super().__init__(message)

        self.message = message
        self.line = line
        self.column = column


class Lexer:
    """Tokenizes source code text into tokens."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

        self.line = 1
        self.column = 1

    # ---------------------------------------------------------
    # Character helpers
    # ---------------------------------------------------------

    @property
    def current(self):
        """Return the current character, or None if at the end of input."""
        if self.pos >= len(self.text):
            return None
        return self.text[self.pos]

    def peek(self, offset=1):
        """Return the character at the given offset from the current position, or None if out of bounds."""
        index = self.pos + offset
        if index >= len(self.text):
            return None
        return self.text[index]

    def advance(self):
        """Advance the current position by one character."""

        if self.current == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        self.pos += 1

    # ---------------------------------------------------------
    # Error
    # ---------------------------------------------------------

    def error(
        self,
        message: str
    ):
        """Raise a LexerError with the given message and current position."""
        raise LexerError(
            message,
            line=self.line,
            column=self.column
        )

    # ---------------------------------------------------------
    # Skip whitespace/comments
    # ---------------------------------------------------------

    def skip_whitespace(self):
        """Skip whitespace characters (spaces, tabs, newlines)."""

        while self.current is not None and self.current.isspace():
            self.advance()

    def skip_single_line_comment(self):
        """Skip a single-line comment starting with //."""

        while self.current not in ("\n", None):
            self.advance()

    def skip_block_comment(self):
        """Skip a block comment starting with /* and ending with */."""

        self.advance()  # /
        self.advance()  # *

        while self.current is not None:

            if self.current == "*" and self.peek() == "/":
                self.advance()
                self.advance()
                return

            self.advance()

        self.error("Unterminated block comment")

    # ---------------------------------------------------------
    # Numbers
    # ---------------------------------------------------------

    def read_number(self):
        """Read a numeric literal from the current input position."""

        start_line = self.line
        start_col = self.column
        text = ""
        has_decimal = False

        while self.current is not None:

            if self.current.isdigit():

                text += self.current

                self.advance()

                continue


            if self.current == ".":

                if has_decimal:

                    break

                has_decimal = True

                text += "."

                self.advance()

                continue


            break


        # ---------------------------------
        # Integer
        # ---------------------------------

        if not has_decimal:

            return Token(

                TokenType.INTEGER,

                int(text),

                start_line,

                start_col,
            )


        # ---------------------------------
        # Float suffix
        # ---------------------------------

        if (
            self.current is not None
            and self.current in ("f", "F")
        ):

            self.advance()

            return Token(

                TokenType.FLOAT,

                float(text),

                start_line,

                start_col,
            )


        # ---------------------------------
        # Double
        # ---------------------------------

        return Token(

            TokenType.DOUBLE,

            float(text),

            start_line,

            start_col,
        )

    # ---------------------------------------------------------
    # Strings
    # ---------------------------------------------------------

    def read_string(self):
        """Read and tokenize a string literal."""

        start_line = self.line
        start_col = self.column

        self.advance()  # opening quote

        value = ""

        escapes = {
            "n": "\n",
            "t": "\t",
            '"': '"',
            "\\": "\\",
        }

        while self.current is not None:

            if self.current == '"':

                self.advance()

                return Token(
                    TokenType.STRING,
                    value,
                    start_line,
                    start_col,
                )

            if self.current == "\\":

                self.advance()

                if self.current is None:
                    return self.error("Invalid escape sequence")

                value += escapes.get(self.current, self.current)
                self.advance()

                continue

            value += self.current
            self.advance()

        self.error("Unterminated string literal")


    # ---------------------------------------------------------
    # Characters
    # ---------------------------------------------------------

    def read_char(self):
        """Read and tokenize a character literal."""

        start_line = self.line
        start_col = self.column

        self.advance()  # opening quote


        if self.current is None:

            self.error(
                "Unterminated character literal"
            )


        escapes = {
            "n": "\n",
            "t": "\t",
            "r": "\r",
            "0": "\0",
            "'": "'",
            '"': '"',
            "\\": "\\",
        }


        # ---------------------------------
        # Escape sequence
        # ---------------------------------

        if self.current == "\\":

            self.advance()


            if self.current is None:

                self.error(
                    "Unterminated character literal"
                )


            value = escapes.get(
                self.current
            )


            if value is None:

                self.error(
                    f"Invalid escape sequence "
                    f"\\{self.current}"
                )


            self.advance()


        # ---------------------------------
        # Normal character
        # ---------------------------------

        else:

            value = self.current

            self.advance()


        # ---------------------------------
        # Closing quote
        # ---------------------------------

        if self.current != "'":

            self.error(
                "Character literal must "
                "contain exactly one character"
            )


        self.advance()


        return Token(
            TokenType.CHAR,
            value,
            start_line,
            start_col,
        )

    # ---------------------------------------------------------
    # Identifiers / keywords
    # ---------------------------------------------------------

    def read_identifier(self):
        """Read and tokenize an identifier or keyword."""

        start_line = self.line
        start_col = self.column

        text = ""

        while (
            self.current is not None
            and (
                self.current.isalnum()
                or self.current == "_"
            )
        ):
            text += self.current
            self.advance()

        token_type = KEYWORDS.get(
            text,
            TokenType.IDENTIFIER,
        )

        return Token(
            token_type,
            text,
            start_line,
            start_col,
        )

    # ---------------------------------------------------------
    # Main tokenizer
    # ---------------------------------------------------------

    def next_token(self):
        """Return the next token from the input text."""

        while self.current is not None:

            # whitespace

            if self.current.isspace():
                self.skip_whitespace()
                continue

            # comments

            if self.current == "/" and self.peek() == "/":
                self.skip_single_line_comment()
                continue

            if self.current == "/" and self.peek() == "*":
                self.skip_block_comment()
                continue

            # identifier

            if (
                self.current.isalpha()
                or self.current == "_"
            ):
                return self.read_identifier()

            # number

            if self.current.isdigit():
                return self.read_number()

            # string

            if self.current == '"':
                return self.read_string()

            # character

            if self.current == "'":
                return self.read_char()

            line = self.line
            column = self.column

            # -------------------------------------------------
            # Two-character operators
            # -------------------------------------------------

            if self.current == "=" and self.peek() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.EQUAL, "==", line, column)

            if self.current == "!" and self.peek() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.NOT_EQUAL, "!=", line, column)

            if self.current == "<" and self.peek() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.LESS_EQUAL, "<=", line, column)

            if self.current == ">" and self.peek() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.GREATER_EQUAL, ">=", line, column)

            if self.current == "&" and self.peek() == "&":
                self.advance()
                self.advance()
                return Token(TokenType.AND, "&&", line, column)

            if self.current == "|" and self.peek() == "|":
                self.advance()
                self.advance()
                return Token(TokenType.OR, "||", line, column)

            # -------------------------------------------------
            # Single-character tokens
            # -------------------------------------------------

            single = {
                "=": TokenType.ASSIGN,
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "<": TokenType.LESS,
                ">": TokenType.GREATER,
                "!": TokenType.NOT,
                "?": TokenType.QUESTION,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                "{": TokenType.LBRACE,
                "}": TokenType.RBRACE,
                ";": TokenType.SEMICOLON,
                ",": TokenType.COMMA,
            }

            if self.current in single:

                ch = self.current
                token = Token(
                    single[ch],
                    ch,
                    line,
                    column,
                )

                self.advance()

                return token

            self.error(
                f"Unexpected character '{self.current}'"
            )

        return Token(
            TokenType.EOF,
            None,
            self.line,
            self.column,
        )

    # ---------------------------------------------------------
    # Utility
    # ---------------------------------------------------------

    def tokenize(self):
        """Tokenize the entire input text and return a list of tokens."""

        tokens = []

        while True:

            token = self.next_token()

            tokens.append(token)

            if token.type == TokenType.EOF:
                break

        return tokens