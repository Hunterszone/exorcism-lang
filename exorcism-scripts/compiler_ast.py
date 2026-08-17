from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from tokens import Token

# ============================================================
# Base AST Node
# ============================================================

@dataclass(slots=True)
class ASTNode:
    """Base class for all AST nodes."""
    line: int
    column: int


@dataclass(slots=True)
class Expression(ASTNode):
    """Base class for all expressions."""
    
# ============================================================
# Program Structure
# ============================================================

@dataclass(slots=True)
class Program(ASTNode):
    """Represents the root of an AST program."""
    statements: List["ASTNode"] = field(default_factory=list)


@dataclass(slots=True)
class Block(ASTNode):
    """Represents a block of statements."""
    statements: List["ASTNode"] = field(default_factory=list)


# ============================================================
# Type Information
# ============================================================

@dataclass(slots=True)
class TypeName(ASTNode):
    """Represents a type name."""

    name: Token

    nullable: bool = False


# ============================================================
# Statements
# ============================================================

@dataclass(slots=True)
class VariableDeclaration(ASTNode):
    """Represents a variable declaration."""

    identifier: Token

    declared_type: Optional[TypeName]

    initializer: ASTNode


@dataclass(slots=True)
class Assignment(ASTNode):
    """Represents an assignment statement."""

    identifier: Token

    value: ASTNode


@dataclass(slots=True)
class ExpressionStatement(ASTNode):
    """Represents an expression statement."""

    expression: ASTNode


@dataclass(slots=True)
class IfStatement(ASTNode):
    """Represents an if statement."""

    condition: ASTNode

    then_block: Block

    else_block: Optional[Block] = None


# ============================================================
# Expressions
# ============================================================

@dataclass(slots=True)
class BinaryExpression(ASTNode):
    """Represents a binary expression."""

    left: ASTNode

    operator: Token

    right: ASTNode


@dataclass(slots=True)
class UnaryExpression(ASTNode):
    """Represents a unary expression."""

    operator: Token

    operand: ASTNode


@dataclass(slots=True)
class VariableReference(ASTNode):
    """Represents a variable reference expression."""

    identifier: Token


# ============================================================
# Literals
# ============================================================

@dataclass(slots=True)
class IntegerLiteral(ASTNode):
    """Represents an integer literal."""

    value: int


@dataclass(slots=True)
class FloatLiteral(ASTNode):
    """Represents a float literal."""

    value: float


@dataclass(slots=True)
class StringLiteral(ASTNode):
    """Represents a string literal."""

    value: str


@dataclass(slots=True)
class BooleanLiteral(ASTNode):
    """Represents a boolean literal."""

    value: bool


@dataclass(slots=True)
class NullLiteral(ASTNode):
    """Represents a null literal."""
    
    
@dataclass
class PrintStatement(ASTNode):
    """Represents a print statement."""

    expression: ASTNode

# ============================================================
# OOP Support
# ============================================================
    
@dataclass
class FunctionDeclaration(ASTNode):
    """Represents a function declaration."""

    return_type: str

    name: str

    parameters: list

    body: Block
    
    token: Token
    
    
@dataclass
class Parameter(ASTNode):
    """Represents a function parameter."""

    parameter_type: TypeName

    name: str
    
    token: Token
    

@dataclass
class FunctionCall(Expression):
    """Represents a function call expression."""

    name: str

    arguments: list[ASTNode]
    
    
@dataclass
class ReturnStatement(ASTNode):
    """Represents a return statement."""

    expression: ASTNode | None