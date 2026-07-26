from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from tokens import Token

# ============================================================
# Base AST Node
# ============================================================

@dataclass(slots=True)
class ASTNode:
    line: int
    column: int


@dataclass(slots=True)
class Expression(ASTNode):
    pass
    
# ============================================================
# Program Structure
# ============================================================

@dataclass(slots=True)
class Program(ASTNode):
    statements: List["ASTNode"] = field(default_factory=list)


@dataclass(slots=True)
class Block(ASTNode):
    statements: List["ASTNode"] = field(default_factory=list)


# ============================================================
# Type Information
# ============================================================

@dataclass(slots=True)
class TypeName(ASTNode):

    name: Token

    nullable: bool = False


# ============================================================
# Statements
# ============================================================

@dataclass(slots=True)
class VariableDeclaration(ASTNode):

    identifier: Token

    declared_type: Optional[TypeName]

    initializer: ASTNode


@dataclass(slots=True)
class Assignment(ASTNode):

    identifier: Token

    value: ASTNode


@dataclass(slots=True)
class ExpressionStatement(ASTNode):

    expression: ASTNode


@dataclass(slots=True)
class IfStatement(ASTNode):

    condition: ASTNode

    then_block: Block

    else_block: Optional[Block] = None


# ============================================================
# Expressions
# ============================================================

@dataclass(slots=True)
class BinaryExpression(ASTNode):

    left: ASTNode

    operator: Token

    right: ASTNode


@dataclass(slots=True)
class UnaryExpression(ASTNode):

    operator: Token

    operand: ASTNode


@dataclass(slots=True)
class VariableReference(ASTNode):

    identifier: Token


# ============================================================
# Literals
# ============================================================

@dataclass(slots=True)
class IntegerLiteral(ASTNode):

    value: int


@dataclass(slots=True)
class FloatLiteral(ASTNode):

    value: float


@dataclass(slots=True)
class StringLiteral(ASTNode):

    value: str


@dataclass(slots=True)
class BooleanLiteral(ASTNode):

    value: bool


@dataclass(slots=True)
class NullLiteral(ASTNode):
    pass
    
    
@dataclass
class PrintStatement(ASTNode):

    expression: ASTNode

# ============================================================
# OOP Support
# ============================================================
    
@dataclass
class FunctionDeclaration(ASTNode):

    return_type: str

    name: str

    parameters: list

    body: list
    
    token: Token
    
    
@dataclass
class Parameter(ASTNode):

    parameter_type: str

    name: str
    
    # token: Token
    

@dataclass
class FunctionCall(Expression):

    name: str

    arguments: list[ASTNode]
    
    
@dataclass
class ReturnStatement(ASTNode):

    expression: ASTNode | None