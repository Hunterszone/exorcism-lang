from __future__ import annotations

from compiler_ast import (
    Program,
    Block,
    VariableDeclaration,
    Assignment,
    ExpressionStatement,
    IfStatement,

    BinaryExpression,
    UnaryExpression,
    VariableReference,

    IntegerLiteral,
    FloatLiteral,
    StringLiteral,
    BooleanLiteral,
    NullLiteral,
    PrintStatement,
)

from tokens import TokenType

from symbols import SymbolTable, SymbolError


class SemanticError(Exception):
    pass



# ============================================================
# Semantic Analyzer
# ============================================================

class SemanticAnalyzer:


    def __init__(self):

        self.symbols = SymbolTable()



    # ========================================================
    # Entry point
    # ========================================================

    def analyze(self, program: Program):

        self.visit(program)



    # ========================================================
    # Dispatcher
    # ========================================================

    def visit(self, node):

        if isinstance(node, Program):

            for statement in node.statements:
                self.visit(statement)


        elif isinstance(node, Block):

            self.visit_block(node)


        elif isinstance(node, VariableDeclaration):

            self.visit_variable_declaration(node)


        elif isinstance(node, Assignment):

            self.visit_assignment(node)


        elif isinstance(node, ExpressionStatement):

            self.evaluate_expression(node.expression)


        elif isinstance(node, IfStatement):

            self.visit_if(node)

        elif isinstance(node, PrintStatement):

            self.evaluate_expression(
                node.expression
            )


        else:

            self.evaluate_expression(node)



    # ========================================================
    # Blocks / scopes
    # ========================================================

    def visit_block(self, block):

        self.symbols.enter_scope()

        try:

            for statement in block.statements:
                self.visit(statement)

        finally:

            self.symbols.exit_scope()



    # ========================================================
    # Variables
    # ========================================================

    def visit_variable_declaration(
        self,
        node: VariableDeclaration
    ):


        expression_type, nullable = (
            self.evaluate_expression(
                node.initializer
            )
        )


        # ---------------------------------
        # var inference
        # ---------------------------------

        if node.declared_type is None:

            final_type = expression_type


        else:

            final_type = (
                node.declared_type.name.value
            )


            declared_nullable = (
                node.declared_type.nullable
            )


            # null assignment check

            if nullable and not declared_nullable:

                raise SemanticError(
                    f"Cannot assign nullable value "
                    f"to non-nullable type "
                    f"'{final_type}' "
                    f"at "
                    f"{node.line}:{node.column}"
                )


            # type mismatch

            if expression_type != "null":

                if final_type != expression_type:

                    raise SemanticError(
                        f"Type mismatch: "
                        f"cannot assign "
                        f"{expression_type} "
                        f"to {final_type}"
                    )


            nullable = declared_nullable



        self.symbols.declare(

            node.identifier,

            final_type,

            nullable,

            initialized=True,
        )



    # ========================================================
    # Assignment
    # ========================================================

    def visit_assignment(
        self,
        node: Assignment
    ):

        symbol = self.symbols.resolve(
            node.identifier
        )


        value_type, nullable = (
            self.evaluate_expression(
                node.value
            )
        )


        if nullable and not symbol.nullable:

            raise SemanticError(
                f"Cannot assign null value "
                f"to non-null variable "
                f"'{symbol.name}'"
            )


        if value_type != "null":

            if symbol.type_name != value_type:

                raise SemanticError(
                    f"Cannot assign "
                    f"{value_type} "
                    f"to "
                    f"{symbol.type_name}"
                )



    # ========================================================
    # If
    # ========================================================

    def visit_if(
        self,
        node: IfStatement
    ):


        condition_type, _ = (
            self.evaluate_expression(
                node.condition
            )
        )


        if condition_type != "bool":

            raise SemanticError(
                "If condition must be boolean"
            )


        self.visit(node.then_block)


        if node.else_block:

            self.visit(node.else_block)



    # ========================================================
    # Expression typing
    # ========================================================

    def evaluate_expression(
        self,
        node
    ):


        # -----------------------------
        # literals
        # -----------------------------

        if isinstance(node, IntegerLiteral):

            return "int", False


        if isinstance(node, FloatLiteral):

            return "float", False


        if isinstance(node, StringLiteral):

            return "String", False


        if isinstance(node, BooleanLiteral):

            return "bool", False


        if isinstance(node, NullLiteral):

            return "null", True



        # -----------------------------
        # variables
        # -----------------------------

        if isinstance(node, VariableReference):

            symbol = self.symbols.resolve(
                node.identifier
            )

            return (
                symbol.type_name,
                symbol.nullable
            )



        # -----------------------------
        # unary
        # -----------------------------

        if isinstance(node, UnaryExpression):

            operand_type, nullable = (
                self.evaluate_expression(
                    node.operand
                )
            )


            if node.operator.type == TokenType.NOT:

                if operand_type != "bool":

                    raise SemanticError(
                        "! requires bool"
                    )

                return "bool", False



            if node.operator.type == TokenType.MINUS:

                if operand_type not in (
                    "int",
                    "float"
                ):

                    raise SemanticError(
                        "- requires number"
                    )

                return operand_type, False



        # -----------------------------
        # binary
        # -----------------------------

        if isinstance(node, BinaryExpression):

            left_type, left_null = (
                self.evaluate_expression(
                    node.left
                )
            )


            right_type, right_null = (
                self.evaluate_expression(
                    node.right
                )
            )


            operator = node.operator.type



            # arithmetic

            if operator in (
                TokenType.PLUS,
                TokenType.MINUS,
                TokenType.STAR,
                TokenType.SLASH,
            ):

                if left_type not in (
                    "int",
                    "float"
                ):

                    raise SemanticError(
                        "Left side must be numeric"
                    )


                if right_type not in (
                    "int",
                    "float"
                ):

                    raise SemanticError(
                        "Right side must be numeric"
                    )


                if (
                    left_type == "float"
                    or right_type == "float"
                ):

                    return "float", False


                return "int", False



            # comparisons

            if operator in (
                TokenType.EQUAL,
                TokenType.NOT_EQUAL,
                TokenType.LESS,
                TokenType.LESS_EQUAL,
                TokenType.GREATER,
                TokenType.GREATER_EQUAL,
            ):

                return "bool", False



            # logical

            if operator in (
                TokenType.AND,
                TokenType.OR,
            ):

                if (
                    left_type != "bool"
                    or right_type != "bool"
                ):

                    raise SemanticError(
                        "Logical operators require bool"
                    )

                return "bool", False



        raise SemanticError(
            "Unknown expression type"
        )