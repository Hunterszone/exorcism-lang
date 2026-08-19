from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    """Enumeration of all token kinds recognized by the lexer."""

    # ---------- Special ----------
    EOF = auto()

    # ---------- Literals ----------
    INTEGER = auto()
    FLOAT = auto()
    DOUBLE = auto()
    CHAR = auto()
    STRING = auto()
    NULL = auto()
    TRUE = auto()
    FALSE = auto()

    # ---------- Identifiers ----------
    IDENTIFIER = auto()

    # ---------- Types ----------
    TYPE_INT = auto()
    TYPE_FLOAT = auto()
    TYPE_DOUBLE = auto()
    TYPE_CHAR = auto()
    TYPE_STRING = auto()
    TYPE_BOOL = auto()
    TYPE_VOID = auto()
    VAR = auto()

    # ---------- Keywords ----------
    IF = auto()
    ELSE = auto()
    PRINT = auto()
    RETURN = auto()
    
    # ---------- Operators ----------
    ASSIGN = auto()        # =
    PLUS = auto()          # +
    MINUS = auto()         # -
    STAR = auto()          # *
    SLASH = auto()         # /

    EQUAL = auto()         # ==
    NOT_EQUAL = auto()     # !=

    LESS = auto()          # <
    LESS_EQUAL = auto()    # <=

    GREATER = auto()       # >
    GREATER_EQUAL = auto() # >=

    AND = auto()           # &&
    OR = auto()            # ||

    NOT = auto()           # !

    QUESTION = auto()      # ?

    # ---------- Delimiters ----------
    LPAREN = auto()
    RPAREN = auto()

    LBRACE = auto()
    RBRACE = auto()

    SEMICOLON = auto()
    COMMA = auto()


@dataclass(slots=True)
class Token:
    """Represents a single token produced by the lexer."""

    type: TokenType
    value: object
    line: int
    column: int

    def __repr__(self):
        return (
            f"Token({self.type.name}, "
            f"{self.value!r}, "
            f"{self.line}:{self.column})"
        )


KEYWORDS = {

    # types
    "int": TokenType.TYPE_INT,
    "float": TokenType.TYPE_FLOAT,
    "double": TokenType.TYPE_DOUBLE,
    "char": TokenType.TYPE_CHAR,
    "String": TokenType.TYPE_STRING,
    "bool": TokenType.TYPE_BOOL,
    "void": TokenType.TYPE_VOID,
    "var": TokenType.VAR,

    # keywords
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "print": TokenType.PRINT,
    "return": TokenType.RETURN,
    
    # literals
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
}