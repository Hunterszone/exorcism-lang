from __future__ import annotations

from compiler_ast import (
    CharLiteral,
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
    
    FunctionDeclaration,
    FunctionCall,
    ReturnStatement,
    TypeName,
)

from tokens import TokenType

from exorcism_types import (
    INT,
    FLOAT,
    DOUBLE,
    BOOL,
    CHAR,
    STRING,
    VOID,
    NULL
)

from type_system import TypeSystem

from symbols import (
    SymbolTable,
    FunctionSymbol,
    Symbol
)

class SemanticError(Exception):
    """Exception raised for semantic analysis errors."""

    def __init__(
        self,
        message,
        token=None
    ):

        super().__init__(message)

        self.message = message

        self.token = token


# ============================================================
# Semantic Analyzer
# ============================================================

class SemanticAnalyzer:
    """Analyzes the abstract syntax tree for semantic correctness and type checking."""

    def __init__(self):

        self.symbols = SymbolTable()
        
        self.type_system = TypeSystem()
        
        self.current_function = None

    # ========================================================
    # Type resolver
    # ========================================================
    
    def resolve_type(
        self,
        type_name
    ):
        """Resolves a type name to its corresponding type, handling nullable types."""

        # ---------------------------------
        # Extract nullable information
        # ---------------------------------

        if isinstance(type_name, TypeName):

            is_nullable = type_name.nullable

            type_name = type_name.name.value

        else:

            is_nullable = type_name.endswith("?")

            if is_nullable:

                type_name = type_name[:-1]


        # ---------------------------------
        # Base type
        # ---------------------------------

        if type_name == "int":

            resolved_type = INT

        elif type_name == "float":

            resolved_type = FLOAT

        elif type_name == "double":
        
            resolved_type = DOUBLE

        elif type_name == "bool":

            resolved_type = BOOL

        elif type_name == "String":

            resolved_type = STRING

        elif type_name == "char":

            resolved_type = CHAR

        elif type_name == "void":

            resolved_type = VOID

        else:

            raise SemanticError(
                f"Unknown type {type_name}"
            )


        # ---------------------------------
        # Nullable modifier
        # ---------------------------------

        if is_nullable:

            if resolved_type == VOID:

                raise SemanticError(
                    "void cannot be nullable"
                )

            return resolved_type.make_nullable()


        return resolved_type


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
            
            
        elif isinstance(node, ReturnStatement):

            self.visit_return(node)
            
            
        elif isinstance(node, FunctionDeclaration):

            self.visit_function_declaration(node)


        elif isinstance(node, FunctionCall):

            self.visit_function_call(node)


        else:

            self.evaluate_expression(node)


    def visit_expression(self, node):

        print(
            "SEMANTIC NODE:",
            type(node).__name__,
            node
        )
        
        if isinstance(node, IntegerLiteral):

            return INT


        if isinstance(node, VariableReference):

            symbol = self.symbols.current_scope.lookup(
                node.identifier.value
            )

            if symbol is None:

                raise SemanticError(
                    f"Undefined variable '{node.identifier.value}'"
                )

            return symbol.type


        # binary operation
        if isinstance(node, BinaryExpression):

            left_type = self.visit_expression(
                node.left
            )

            right_type = self.visit_expression(
                node.right
            )


            if left_type != right_type:

                raise SemanticError(
                    "Binary operation type mismatch"
                )


            return left_type


        raise SemanticError(
            f"Unknown expression type: {type(node).__name__}"
        )
        
    
    def visit_return(self, node):

        if self.current_function is None:

            raise SemanticError(
                "Return statement outside function"
            )

        
        if self.current_function.return_type is VOID:

            if node.expression is not None:

                raise SemanticError(
                    "Void function cannot return a value"
                )

            return
            
        
        if node.expression is None:

            raise SemanticError(
                "Non-void function must return a value"
            )
            
            
        # return expression;

        return_type = self.evaluate_expression(
            node.expression
        )


        if not self.type_system.is_assignable(
            return_type,
            self.current_function.return_type
        ):

            raise SemanticError(
                f"Return type mismatch: "
                f"expected {self.current_function.return_type}, "
                f"got {return_type}"
            )


    # ========================================================
    # Blocks / scopes
    # ========================================================

    def visit_block(
        self, 
        block
    ):

        self.symbols.enter_scope(
            start_line=block.line,
            start_column=block.column,
        )

        try:

            for statement in block.statements:
                self.visit(statement)

        finally:

            self.symbols.exit_scope(
                end_line=block.line,
                end_column=block.column,
            )


    # ========================================================
    # Variables
    # ========================================================

    def visit_variable_declaration(
        self,
        node: VariableDeclaration
    ):


        expression_type = (
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

            final_type = self.resolve_type(
                node.declared_type.name.value
            )
            

            if node.declared_type.nullable:

                final_type = final_type.make_nullable()


            if not self.type_system.is_assignable(
                expression_type,
                final_type
            ):

                raise SemanticError(
                    f"Cannot assign "
                    f"{expression_type} "
                    f"to "
                    f"{final_type} ",
                    token=node.identifier

                )


        self.symbols.declare(

            node.identifier,

            final_type,

            initialized=True,
        )


    # ========================================================
    # Functions
    # ========================================================
    
    def visit_function_declaration(
        self,
        node
    ):

        resolved_return_type = self.resolve_type(
            node.return_type
        )

        node.return_type = resolved_return_type

        parameter_symbols = []

        for parameter in node.parameters:

            parameter.parameter_type = (
                self.resolve_type(
                    parameter.parameter_type
                )
            )

            parameter_symbol = Symbol(

                name=parameter.name,

                token=parameter.token,

                type=parameter.parameter_type,

                initialized=True
            )

            parameter_symbols.append(
                parameter_symbol
            )

        symbol = FunctionSymbol(

            name=node.name,

            token=node.token,

            type=resolved_return_type,

            return_type=resolved_return_type,

            initialized=True,

            parameters=parameter_symbols
        )

        self.symbols.current_scope.define(
            symbol
        )

        self.symbols.enter_scope(
            start_line=node.body.line,
            start_column=node.body.column,
        )

        self.current_function = symbol

        try:

            for parameter_symbol in parameter_symbols:

                self.symbols.current_scope.define(
                    parameter_symbol
                )

            for statement in node.body.statements:

                self.visit(statement)

        finally:

            self.current_function = None

            self.symbols.exit_scope(
                end_line=node.body.line,
                end_column=node.body.column,
            )


    def visit_function_call(
        self,
        node
    ):

        symbol = self.symbols.current_scope.lookup(
            node.name
        )


        if symbol is None:

            raise SemanticError(
                f"Unknown function '{node.name}'"
            )


        if not isinstance(
            symbol,
            FunctionSymbol
        ):

            raise SemanticError(
                f"'{node.name}' is not a function"
            )


        if len(node.arguments) != len(
            symbol.parameters
        ):

            raise SemanticError(
                f"Function '{node.name}' expects "
                f"{len(symbol.parameters)} arguments"
            )


        for argument, parameter in zip(
            node.arguments,
            symbol.parameters
        ):

            argument_type = self.evaluate_expression(
                argument
            )

            if argument_type != parameter.type:

                raise SemanticError(
                    f"Argument type mismatch in '{node.name}'"
                )


        return symbol.return_type
    
        
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


        value_type = (
            self.evaluate_expression(
                node.value
            )
        )


        if not self.type_system.is_assignable(
            value_type,
            symbol.type
        ):

            raise SemanticError(
                f"Cannot assign "
                f"{value_type} "
                f"to "
                f"{symbol.type}",
                token=node.identifier
            )



    # ========================================================
    # If
    # ========================================================

    def visit_if(
        self,
        node: IfStatement
    ):


        condition_type = (
            self.evaluate_expression(
                node.condition
            )
        )


        if condition_type != BOOL:

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
        """Return the semantic type of an expression."""

        # -----------------------------
        # literals
        # -----------------------------

        if isinstance(node, IntegerLiteral):

            return INT


        if isinstance(node, FloatLiteral):

            if node.token_type == TokenType.FLOAT:

                return FLOAT


            if node.token_type == TokenType.DOUBLE:

                return DOUBLE


            raise SemanticError(
                f"Unknown floating-point literal "
                f"type: {node.token_type}"
            )


        if isinstance(node, CharLiteral):

            return CHAR


        if isinstance(node, StringLiteral):

            return STRING


        if isinstance(node, BooleanLiteral):

            return BOOL


        if isinstance(node, NullLiteral):

            return NULL



        # -----------------------------
        # variables
        # -----------------------------

        if isinstance(node, VariableReference):

            symbol = self.symbols.resolve(
                node.identifier
            )

            return (
                symbol.type
            )

        
        # -----------------------------
        # function call
        # -----------------------------

        if isinstance(node, FunctionCall):

            symbol = self.symbols.lookup_name(
                node.name
            )

            if symbol is None:

                raise SemanticError(
                    f"Unknown function '{node.name}'"
                )


            if not isinstance(
                symbol,
                FunctionSymbol
            ):

                raise SemanticError(
                    f"'{node.name}' is not a function"
                )


            if symbol.return_type is VOID:

                return VOID


            if len(node.arguments) != len(
                symbol.parameters
            ):

                raise SemanticError(
                    f"Function '{node.name}' expects "
                    f"{len(symbol.parameters)} arguments"
                )


            for argument, parameter in zip(
                node.arguments,
                symbol.parameters
            ):

                argument_type = (
                    self.evaluate_expression(
                        argument
                    )
                )


                if argument_type != parameter.parameter_type:

                    raise SemanticError(
                        f"Argument type mismatch in "
                        f"function '{node.name}'"
                    )


            return symbol.return_type

        # -----------------------------
        # unary
        # -----------------------------

        if isinstance(node, UnaryExpression):

            operand_type = (
                self.evaluate_expression(
                    node.operand
                )
            )


            if node.operator.type == TokenType.NOT:

                if operand_type != BOOL:

                    raise SemanticError(
                        "! requires bool"
                    )

                return BOOL



            if node.operator.type == TokenType.MINUS:

                if operand_type not in (
                    INT,
                    FLOAT
                ):

                    raise SemanticError(
                        "- requires number"
                    )

                return operand_type



        # -----------------------------
        # binary
        # -----------------------------

        if isinstance(node, BinaryExpression):

            left_type = (
                self.evaluate_expression(
                    node.left
                )
            )


            right_type = (
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
                    INT,
                    FLOAT
                ):

                    raise SemanticError(
                        "Left side must be numeric"
                    )


                if right_type not in (
                    INT,
                    FLOAT
                ):

                    raise SemanticError(
                        "Right side must be numeric"
                    )


                if (
                    left_type == FLOAT
                    or right_type == FLOAT
                ):

                    return FLOAT


                return INT



            # comparisons

            if operator in (
                TokenType.EQUAL,
                TokenType.NOT_EQUAL,
                TokenType.LESS,
                TokenType.LESS_EQUAL,
                TokenType.GREATER,
                TokenType.GREATER_EQUAL,
            ):

                return BOOL



            # logical

            if operator in (
                TokenType.AND,
                TokenType.OR,
            ):

                if (
                    left_type != BOOL
                    or right_type != BOOL
                ):

                    raise SemanticError(
                        "Logical operators require bool"
                    )

                return BOOL



        raise SemanticError(
            "Unknown expression type"
        )