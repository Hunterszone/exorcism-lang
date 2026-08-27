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
    """Raised when semantic analysis encounters an invalid program construct."""

    def __init__(
        self,
        message,
        token=None,
        node=None
    ):
        super().__init__(
            message
        )

        self.message = message
        self.token = token
        self.node = node


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
        """Resolve a type name to its corresponding Type."""

        # ---------------------------------
        # Validate input
        # ---------------------------------

        if type_name is None:

            raise SemanticError(
                "Cannot resolve a missing type"
            )


        # ---------------------------------
        # Extract nullable information
        # ---------------------------------

        if isinstance(
            type_name,
            TypeName
        ):

            is_nullable = (
                type_name.nullable
            )

            type_name = (
                type_name.name.value
            )

        elif isinstance(
            type_name,
            str
        ):

            is_nullable = (
                type_name.endswith("?")
            )

            if is_nullable:

                type_name = (
                    type_name[:-1]
                )

        else:

            raise SemanticError(
                f"Invalid type name: {type(type_name).__name__}"
            )


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
        """Analyze the program and perform semantic validation."""

        self.visit(program)



    # ========================================================
    # Dispatcher
    # ========================================================

    def visit(self, node):
        """Dispatch to the appropriate visit method based on the node type."""

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
        """Evaluate the type of an expression node and return its semantic type."""
        
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

            return symbol.type_properties


        # binary operation
        if isinstance(node, BinaryExpression):

            left_type = self.visit_expression(
                node.left
            )

            right_type = self.visit_expression(
                node.right
            )


            # ---------------------------------
            # String concatenation
            # ---------------------------------

            if node.operator.type == TokenType.PLUS:

                if left_type == STRING and right_type == STRING:

                    return STRING


            if left_type != right_type:

                raise SemanticError(
                    "Binary operation type mismatch"
                )


            return left_type


        raise SemanticError(
            f"Unknown expression type: {type(node).__name__}"
        )
        
    
    def visit_return(self, node):
        """Handle return statements, ensuring they match the current function's return type."""

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
        """Visit a block of statements, creating a new scope for variable declarations."""

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
        """Handle variable declarations, resolving types and checking initializers."""


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
                node.declared_type
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
        """Handle function declarations, resolving return and parameter types."""

        resolved_return_type = self.resolve_type(
            node.return_type
        )


        node.return_type = resolved_return_type


        parameter_symbols = []


        for parameter in node.parameters:

            parameter.resolved_type = self.resolve_type(
                parameter.parameter_type
            )


            parameter_symbol = Symbol(

                name=parameter.name,

                token=parameter.token,

                type_properties=parameter.resolved_type,

                initialized=True
            )


            parameter_symbols.append(
                parameter_symbol
            )


        symbol = FunctionSymbol(

            name=node.name,

            token=node.token,

            type_properties=resolved_return_type,

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


    # ========================================================
    # Function calls
    # ========================================================

    def visit_function_call(
        self,
        node
    ):
        """Handle function calls, resolving the function symbol and checking argument types."""

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

            if not self.type_system.is_assignable(
                argument_type,
                parameter.type_properties
            ):

                raise SemanticError(
                    f"Argument type mismatch in "
                    f"'{node.name}'",
                    node=argument
                )


        return symbol.return_type
    
        
    # ========================================================
    # Assignment
    # ========================================================

    def visit_assignment(
        self,
        node: Assignment
    ):
        """Handle assignment statements, ensuring the variable exists and the assigned value is compatible with its type."""

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
            symbol.type_properties
        ):

            raise SemanticError(
                f"Cannot assign "
                f"{value_type} "
                f"to "
                f"{symbol.type_properties}",
                token=node.identifier
            )



    # ========================================================
    # If
    # ========================================================

    def visit_if(
        self,
        node: IfStatement
    ):
        """Handle if/option/else conditional chains."""

        # ---------------------------------
        # IF condition
        # ---------------------------------

        condition_type = (
            self.evaluate_expression(
                node.condition
            )
        )


        if condition_type != BOOL:

            raise SemanticError(
                "If condition must be boolean",
                node=node.condition
            )


        self.visit(
            node.then_block
        )


        # ---------------------------------
        # OPTION conditions
        # ---------------------------------

        for option_condition, option_block in (
            node.alternatives
        ):

            option_type = (
                self.evaluate_expression(
                    option_condition
                )
            )


            if option_type != BOOL:

                raise SemanticError(
                    "Option condition must be boolean",
                    node=option_condition
                )


            self.visit(
                option_block
            )


        # ---------------------------------
        # ELSE
        # ---------------------------------

        if node.else_block:

            self.visit(
                node.else_block
            )



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
                symbol.type_properties
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
                    f"Unknown function '{node.name}'",
                    node=node
                )


            if not isinstance(
                symbol,
                FunctionSymbol
            ):

                raise SemanticError(
                    f"'{node.name}' is not a function",
                    node=node
                )


            # Check argument count for ALL functions,
            # including void functions.

            if len(node.arguments) != len(
                symbol.parameters
            ):

                raise SemanticError(
                    f"Function '{node.name}' expects "
                    f"{len(symbol.parameters)} arguments",
                    node=node
                )


            # Check argument types.

            for argument, parameter in zip(
                node.arguments,
                symbol.parameters
            ):

                argument_type = (
                    self.evaluate_expression(
                        argument
                    )
                )


                if not self.type_system.is_assignable(
                    argument_type,
                    parameter.type_properties
                ):

                    raise SemanticError(
                        f"Argument type mismatch in "
                        f"'{node.name}'",
                        node=argument
                    )


            # Void functions have no expression value.

            if symbol.return_type is VOID:

                return VOID


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
                    FLOAT,
                    DOUBLE
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

            # ---------------------------------
            # Addition
            # ---------------------------------

            if operator == TokenType.PLUS:

                # String concatenation

                if (
                    left_type == STRING
                    and
                    right_type == STRING
                ):

                    return STRING


                # Numeric addition

                if (
                    self.is_numeric_type(left_type)
                    and
                    self.is_numeric_type(right_type)
                ):

                    return self.promote_numeric_types(
                        left_type,
                        right_type
                    )


                raise SemanticError(
                    "Operands must be numeric or both strings"
                )


            # ---------------------------------
            # Other arithmetic
            # ---------------------------------

            if operator in (
                TokenType.MINUS,
                TokenType.STAR,
                TokenType.SLASH,
            ):

                if not self.is_numeric_type(
                    left_type
                ):

                    raise SemanticError(
                        "Left side must be numeric",
                        node=node.left
                    )


                if not self.is_numeric_type(
                    right_type
                ):

                    raise SemanticError(
                        "Right side must be numeric",
                        node=node.right
                    )


                return self.promote_numeric_types(
                    left_type,
                    right_type
                )


            # ---------------------------------
            # Comparisons
            # ---------------------------------

            if operator in (
                TokenType.EQUAL,
                TokenType.NOT_EQUAL,
                TokenType.LESS,
                TokenType.LESS_EQUAL,
                TokenType.GREATER,
                TokenType.GREATER_EQUAL,
            ):

                equality_operator = operator in (
                    TokenType.EQUAL,
                    TokenType.NOT_EQUAL,
                )


                # ---------------------------------
                # Numeric comparison
                # ---------------------------------

                if (
                    self.is_numeric_type(left_type)
                    and
                    self.is_numeric_type(right_type)
                ):

                    self.promote_numeric_types(
                        left_type,
                        right_type
                    )

                    return BOOL


                # ---------------------------------
                # Character comparison
                # ---------------------------------

                if (
                    left_type == CHAR
                    and
                    right_type == CHAR
                ):

                    return BOOL


                # ---------------------------------
                # String equality
                # ---------------------------------

                if (
                    left_type == STRING
                    and
                    right_type == STRING
                ):

                    if equality_operator:

                        return BOOL


                    raise SemanticError(
                        "String ordering is not supported"
                    )


                # ---------------------------------
                # Boolean equality
                # ---------------------------------

                if (
                    left_type == BOOL
                    and
                    right_type == BOOL
                ):

                    if equality_operator:

                        return BOOL


                    raise SemanticError(
                        "Boolean ordering is not supported"
                    )


                raise SemanticError(
                    "Incompatible types for comparison"
                )


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


    #========================================================
    # Numeric type handling
    #========================================================

    def is_numeric_type(
        self,
        type_
    ):
        """Return True when the type is numeric."""

        return type_ in (
            INT,
            FLOAT,
            DOUBLE,
        )


    #========================================================
    # Numeric type promotion
    #========================================================

    def promote_numeric_types(
        self,
        left_type,
        right_type
    ):
        """Return the common numeric type for two numeric operands."""

        if not self.is_numeric_type(
            left_type
        ):

            raise SemanticError(
                f"Expected numeric type, "
                f"got {left_type}"
            )


        if not self.is_numeric_type(
            right_type
        ):

            raise SemanticError(
                f"Expected numeric type, "
                f"got {right_type}"
            )


        # DOUBLE has highest precedence.

        if (
            left_type == DOUBLE
            or
            right_type == DOUBLE
        ):

            return DOUBLE


        # FLOAT has second-highest precedence.

        if (
            left_type == FLOAT
            or
            right_type == FLOAT
        ):

            return FLOAT


        # Both operands are INT.

        return INT


    def collect_symbols(self, ast):
        """
        Collect declarations into the symbol table without
        performing semantic validation.
        """

        self._collect_symbols(ast)

        return self.symbols


    def _collect_symbols(self, node):

        if isinstance(node, Program):

            for statement in node.statements:
                self._collect_symbols(statement)

            return


        # Is Block instance

        if isinstance(node, Block):

            for statement in node.statements:
                self._collect_symbols(statement)

            return


        # Is VariableDeclaration instance

        if isinstance(node, VariableDeclaration):

            # ---------------------------------------------
            # Resolve declared type or infer from initializer
            # ---------------------------------------------

            if node.declared_type is None:

                if node.initializer is None:

                    raise SemanticError(
                        f"Variable '{node.identifier.value}' "
                        "requires a type or initializer",
                        token=node.identifier
                    )

                variable_type = self.evaluate_expression(
                    node.initializer
                )

            else:

                variable_type = self.resolve_type(
                    node.declared_type
                )


            # ---------------------------------------------
            # Create symbol
            # ---------------------------------------------

            symbol = Symbol(
                name=str(
                    node.identifier.value
                ),

                token=node.identifier,

                type_properties=variable_type,

                initialized=node.initializer is not None,
            )


            self.symbols.current_scope.define(
                symbol
            )

            return


        # Is FunctionDeclaration instance

        if isinstance(
            node,
            FunctionDeclaration
        ):

            # ---------------------------------------------
            # Resolve return type
            # ---------------------------------------------

            return_type = self.resolve_type(
                node.return_type
            )


            # ---------------------------------------------
            # Resolve parameters
            # ---------------------------------------------

            parameter_symbols = []


            for parameter in node.parameters:

                parameter_type = self.resolve_type(
                    parameter.parameter_type
                )


                parameter_symbol = Symbol(
                    name=parameter.name,

                    token=parameter.token,

                    type_properties=parameter_type,

                    initialized=True,
                )


                parameter_symbols.append(
                    parameter_symbol
                )


            # ---------------------------------------------
            # Create complete function symbol
            # ---------------------------------------------

            function_symbol = FunctionSymbol(
                name=node.name,

                token=node.token,

                type_properties=return_type,

                return_type=return_type,

                parameters=parameter_symbols,

                initialized=True,
            )


            self.symbols.current_scope.define(
                function_symbol
            )


            # ---------------------------------------------
            # Enter function scope
            # ---------------------------------------------

            self.symbols.enter_scope(
                start_line=node.token.line,
                start_column=node.token.column,
            )


            # ---------------------------------------------
            # Define parameters inside function scope
            # ---------------------------------------------

            for parameter_symbol in parameter_symbols:

                self.symbols.current_scope.define(
                    parameter_symbol
                )


            # ---------------------------------------------
            # Collect function body
            # ---------------------------------------------

            self._collect_symbols(
                node.body
            )


            # ---------------------------------------------
            # Leave function scope
            # ---------------------------------------------

            if node.body.end_token is not None:

                self.symbols.exit_scope(
                    end_line=node.body.end_token.line,
                    end_column=node.body.end_token.column,
                )

            else:

                self.symbols.exit_scope()


            return