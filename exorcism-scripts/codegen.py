from __future__ import annotations

from llvmlite import ir

from exorcism_types import (
    TypeProperties,
    ClassType,
    NullableType,

    INT,
    FLOAT,
    DOUBLE,
    BOOL,
    CHAR,
    STRING,
    VOID
)

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
    BooleanLiteral,
    StringLiteral,
    CharLiteral,
    NullLiteral,
    PrintStatement,
    
    FunctionDeclaration,
    FunctionCall,
    ReturnStatement,
)

from tokens import TokenType


class CodeGenerationError(Exception):
    """Custom exception for code generation errors."""


class LLVMCodeGenerator:
    """LLVM code generator for the MiniCompiler."""

    def __init__(self):

        self.module = ir.Module(
            name="MiniCompilerModule"
        )
        
        self.module.add_named_metadata(
            "wasm.memory"
        )


        #---------------------------------
        # Print function
        #---------------------------------

        self.print_string = ir.Function(
            self.module,
            ir.FunctionType(
                ir.VoidType(),
                [
                    ir.IntType(8).as_pointer()
                ]
            ),
            name="print_string"
        )


        #---------------------------------
        # String concatenation function
        #---------------------------------

        self.concat_strings = ir.Function(
            self.module,
            ir.FunctionType(
                ir.IntType(8).as_pointer(),
                [
                    ir.IntType(8).as_pointer(),
                    ir.IntType(8).as_pointer()
                ]
            ),
            name="concat_strings"
        )
        

        #---------------------------------
        # Print integer function
        #---------------------------------

        self.print_int = ir.Function(
            self.module,
            ir.FunctionType(
                ir.VoidType(),
                [
                    ir.IntType(32)
                ]
            ),
            name="print_int"
        )


        self.function = None

        self.builder = None


        # variables & functions -> llvm pointer

        self.variables = {}
        self.functions = {}


    def generate(self, program: Program):
        """Generate LLVM IR for the given program AST."""

        # ============================================================
        # Create program entry point
        # ============================================================

        function_type = ir.FunctionType(
            ir.IntType(32),
            []
        )


        self.function = ir.Function(
            self.module,
            function_type,
            name="main"
        )


        entry = self.function.append_basic_block(
            name="entry"
        )


        self.builder = ir.IRBuilder(entry)


        # ============================================================
        # Generate program
        # ============================================================

        self.visit(program)


        # ============================================================
        # Default main return
        # ============================================================

        if not self.builder.block.is_terminated:

            self.builder.ret(
                ir.Constant(
                    ir.IntType(32),
                    0
                )
            )


        return self.module


    # Generate function
    
    def generate_function(self, node):
        """Generate LLVM function from function node."""

        return_type = self.get_llvm_type(
            node.return_type
        )


        arguments = []

        for parameter in node.parameters:

            arguments.append(
                self.get_llvm_type(
                    parameter.resolved_type
                )
            )


        function_type = ir.FunctionType(
            return_type,
            arguments
        )


        function = ir.Function(
            self.module,
            function_type,
            name=node.name
        )

        self.functions[node.name] = function


        # ---------------------------------
        # Save generator state
        # ---------------------------------

        old_builder = self.builder
        old_variables = self.variables
        old_function = self.function


        # ---------------------------------
        # Enter function
        # ---------------------------------

        self.function = function

        block = function.append_basic_block(
            name="entry"
        )

        self.builder = ir.IRBuilder(
            block
        )

        self.variables = {}


        # ---------------------------------
        # Parameters
        # ---------------------------------

        for index, parameter in enumerate(
            node.parameters
        ):

            llvm_parameter = function.args[index]

            llvm_parameter.name = parameter.name


            pointer = self.builder.alloca(
                llvm_parameter.type,
                name=f"{parameter.name}_addr"
            )


            self.builder.store(
                llvm_parameter,
                pointer
            )


            self.variables[
                parameter.name
            ] = pointer


        # ---------------------------------
        # Function body
        # ---------------------------------

        for statement in node.body.statements:

            self.visit(statement)


        # ---------------------------------
        # Safety return
        # ---------------------------------

        if not self.builder.block.is_terminated:

            if node.return_type == VOID:

                self.builder.ret_void()

            else:

                self.builder.ret(
                    ir.Constant(
                        return_type,
                        0
                    )
                )


        # ---------------------------------
        # Restore state
        # ---------------------------------

        self.builder = old_builder
        self.variables = old_variables
        self.function = old_function


    # Get LLVM type

    def get_llvm_type(self, type_obj: TypeProperties):
        """Map a MiniCompiler type to an LLVM type."""

        # ---------------------------------
        # Nullable types
        # ---------------------------------

        if isinstance(type_obj, NullableType):

            return self.get_llvm_type(
                type_obj.base_type
            )


        # ---------------------------------
        # Primitive types
        # ---------------------------------

        if type_obj is INT:

            return ir.IntType(32)


        if type_obj is FLOAT:

            return ir.FloatType()


        if type_obj is DOUBLE:

            return ir.DoubleType()


        if type_obj is BOOL:

            return ir.IntType(1)


        if type_obj is CHAR:

            return ir.IntType(8)


        if type_obj is VOID:

            return ir.VoidType()


        # ---------------------------------
        # Reference types
        # ---------------------------------

        if type_obj is STRING:

            # temporary representation
            # until %String runtime object is introduced

            return ir.IntType(8).as_pointer()


        if isinstance(type_obj, ClassType):

            # future:
            #
            # %Person*
            #
            # %Animal*

            return ir.IntType(8).as_pointer()


        raise Exception(
            f"Unknown type '{type_obj}'"
        )
    
    # ========================================================
    # Dispatcher
    # ========================================================

    def visit(self, node):
        """Dispatch to the appropriate visit method based on the node type."""


        if isinstance(node, Program):

            for statement in node.statements:

                self.visit(statement)



        elif isinstance(node, Block):

            for statement in node.statements:

                self.visit(statement)



        elif isinstance(node, VariableDeclaration):

            self.visit_variable(node)



        elif isinstance(node, Assignment):

            self.visit_assignment(node)



        elif isinstance(node, ExpressionStatement):

            self.generate_expression(
                node.expression
            )

        
        elif isinstance(node, IfStatement):

            self.visit_if(node)

        
        
        elif isinstance(node, PrintStatement):

            self.visit_print(node)
            
         
        elif isinstance(node, FunctionDeclaration):

            self.generate_function(node)
            
        
        elif isinstance(node, ReturnStatement):

            self.visit_return(node)
            
            
    # ========================================================
    # Print
    # ========================================================
    
    def visit_print(self, node):
        """Handle print statements, generating code to print the evaluated expression."""

        value = self.generate_expression(
            node.expression
        )


        if isinstance(value.type, ir.IntType):

            self.builder.call(
                self.print_int,
                [value]
            )


        elif isinstance(value.type, ir.PointerType):

            self.builder.call(
                self.print_string,
                [value]
            )


        else:

            raise CodeGenerationError(
                f"Cannot print type {value.type}"
            )
        
    # ========================================================
    # Return
    # ========================================================
    
    def visit_return(self, node):
        """Handle return statements, generating code to return the evaluated expression or void."""

        # return;

        if node.expression is None:

            raise Exception(
                "Non-void function must return a value"
            )


        # return expression;

        value = self.generate_expression(
            node.expression
        )


        self.builder.ret(
            value
        )
    
    
    # ========================================================
    # Variables
    # ========================================================

    def llvm_type(self, value):
        """Return the LLVM type for a given literal value."""

        if isinstance(value, IntegerLiteral):

            return ir.IntType(32)


        if isinstance(value, BooleanLiteral):

            return ir.IntType(1)


        if isinstance(value, FloatLiteral):

            return ir.FloatType()


        return ir.IntType(32)


    # Variable Declarations and Assignments

    def visit_variable(
        self,
        node
    ):
        """Handle variable declarations, allocating space and initializing the variable."""

        value = self.generate_expression(
            node.initializer
        )


        variable_type = value.type


        ptr = self.builder.alloca(
            variable_type,
            name=node.identifier.value
        )


        self.builder.store(
            value,
            ptr
        )


        self.variables[
            node.identifier.value
        ] = ptr



    def visit_assignment(
        self,
        node
    ):
        """Handle assignment statements, ensuring the variable exists and the assigned value is compatible with its type."""

        if node.identifier.value not in self.variables:

            raise CodeGenerationError(
                f"Unknown variable "
                f"{node.identifier.value}"
            )


        ptr = self.variables[
            node.identifier.value
        ]


        value = self.generate_expression(
            node.value
        )


        self.builder.store(
            value,
            ptr
        )



    # ========================================================
    # If / Option / Else
    # ========================================================

    def visit_if(
        self,
        node
    ):
        """Generate LLVM IR for an if/option/else conditional chain."""

        # =====================================================
        # MERGE
        # =====================================================

        merge_block = (
            self.function.append_basic_block(
                "merge"
            )
        )


        # =====================================================
        # THEN
        # =====================================================

        then_block = (
            self.function.append_basic_block(
                "then"
            )
        )


        # =====================================================
        # OPTION CONDITION BLOCKS
        # =====================================================

        option_condition_blocks = []


        for index in range(
            len(node.alternatives)
        ):

            option_condition_blocks.append(
                self.function.append_basic_block(
                    f"option_{index}"
                )
            )


        # =====================================================
        # ELSE
        # =====================================================

        else_block = None


        if node.else_block:

            else_block = (
                self.function.append_basic_block(
                    "else"
                )
            )


        # =====================================================
        # FIRST IF CONDITION
        # =====================================================

        condition = (
            self.generate_expression(
                node.condition
            )
        )


        if node.alternatives:

            false_block = (
                option_condition_blocks[0]
            )

        elif else_block:

            false_block = else_block

        else:

            false_block = merge_block


        self.builder.cbranch(
            condition,
            then_block,
            false_block
        )


        # =====================================================
        # THEN
        # =====================================================

        self.builder.position_at_end(
            then_block
        )


        self.visit(
            node.then_block
        )


        if not self.builder.block.is_terminated:

            self.builder.branch(
                merge_block
            )


        # =====================================================
        # OPTIONS
        # =====================================================

        for index, (
            option_condition,
            option_body
        ) in enumerate(
            node.alternatives
        ):

            option_condition_block = (
                option_condition_blocks[index]
            )


            option_then_block = (
                self.function.append_basic_block(
                    f"option_{index}_then"
                )
            )


            # ---------------------------------------------
            # Determine false destination
            # ---------------------------------------------

            if index + 1 < len(
                option_condition_blocks
            ):

                next_false_block = (
                    option_condition_blocks[
                        index + 1
                    ]
                )

            elif else_block:

                next_false_block = (
                    else_block
                )

            else:

                next_false_block = (
                    merge_block
                )


            # ---------------------------------------------
            # OPTION CONDITION
            # ---------------------------------------------

            self.builder.position_at_end(
                option_condition_block
            )


            option_value = (
                self.generate_expression(
                    option_condition
                )
            )


            self.builder.cbranch(
                option_value,
                option_then_block,
                next_false_block
            )


            # ---------------------------------------------
            # OPTION BODY
            # ---------------------------------------------

            self.builder.position_at_end(
                option_then_block
            )


            self.visit(
                option_body
            )


            if not self.builder.block.is_terminated:

                self.builder.branch(
                    merge_block
                )


        # =====================================================
        # ELSE
        # =====================================================

        if else_block:

            self.builder.position_at_end(
                else_block
            )


            self.visit(
                node.else_block
            )


            if not self.builder.block.is_terminated:

                self.builder.branch(
                    merge_block
                )


        # =====================================================
        # MERGE
        # =====================================================

        self.builder.position_at_end(
            merge_block
        )


    # ========================================================
    # Expressions
    # ========================================================

    def generate_expression(
        self,
        node
    ):
        """Generate LLVM IR for the given expression AST node."""


        # integer

        if isinstance(node, IntegerLiteral):

            return ir.Constant(
                ir.IntType(32),
                node.value
            )


        # float & double

        if isinstance(node, FloatLiteral):

            if node.token_type == TokenType.FLOAT:

                return ir.Constant(
                    ir.FloatType(),
                    node.value
                )


            if node.token_type == TokenType.DOUBLE:

                return ir.Constant(
                    ir.DoubleType(),
                    node.value
                )


            raise CodeGenerationError(
                f"Unknown floating-point literal "
                f"type: {node.token_type}"
            )


        # bool

        if isinstance(node, BooleanLiteral):

            return ir.Constant(
                ir.IntType(1),
                1 if node.value else 0
            )


        # character literal

        if isinstance(node, CharLiteral):

            return ir.Constant(
                ir.IntType(8),
                ord(node.value)
            )


        # string literal

        if isinstance(node, StringLiteral):

            text = node.value + "\0"


            string_type = ir.ArrayType(
                ir.IntType(8),
                len(text)
            )


            string_constant = ir.GlobalVariable(
                self.module,
                string_type,
                name=f"str_{len(self.module.globals)}"
            )


            string_constant.global_constant = True


            string_constant.initializer = ir.Constant(
                string_type,
                bytearray(
                    text.encode("utf8")
                )
            )


            return self.builder.bitcast(
                string_constant,
                ir.IntType(8).as_pointer()
            )


        # null

        if isinstance(node, NullLiteral):

            return ir.Constant(
                ir.IntType(32),
                0
            )



        # variable lookup

        if isinstance(node, VariableReference):

            variable_name = node.identifier.value

            ptr = self.variables.get(
                node.identifier.value
            )


            if ptr is None:

                raise CodeGenerationError(
                    f"Unknown variable "
                    f"{variable_name}"
                )


            return self.builder.load(
                ptr,
                name=f"{variable_name}_value"
            )



        # unary

        if isinstance(node, UnaryExpression):

            value = self.generate_expression(
                node.operand
            )


            if node.operator.type == TokenType.NOT:

                return self.builder.xor(
                    value,
                    ir.Constant(
                        ir.IntType(1),
                        1
                    )
                )


            if node.operator.type == TokenType.MINUS:

                return self.builder.neg(
                    value
                )



        # binary

        if isinstance(node, BinaryExpression):


            left = self.generate_expression(
                node.left
            )


            right = self.generate_expression(
                node.right
            )


            op = node.operator.type


            # Addition

            if op == TokenType.PLUS:


                # String concatenation

                if (
                    isinstance(left.type, ir.PointerType)
                    and
                    isinstance(right.type, ir.PointerType)
                ):

                    return self.builder.call(
                        self.concat_strings,
                        [
                            left,
                            right
                        ],
                        name="concat"
                    )


                # Numeric addition

                return self.builder.add(
                    left,
                    right,
                    "addtmp"
                )


            # Subtraction

            if op == TokenType.MINUS:

                return self.builder.sub(
                    left,
                    right,
                    "subtmp"
                )


            # Multiplication

            if op == TokenType.STAR:

                return self.builder.mul(
                    left,
                    right,
                    "multmp"
                )


            # Division

            if op == TokenType.SLASH:

                return self.builder.sdiv(
                    left,
                    right,
                    "divtmp"
                )



            # Comparisons

            if op == TokenType.EQUAL:

                return self.builder.icmp_signed(
                    "==",
                    left,
                    right
                )


            if op == TokenType.NOT_EQUAL:

                return self.builder.icmp_signed(
                    "!=",
                    left,
                    right
                )


            if op == TokenType.LESS:

                return self.builder.icmp_signed(
                    "<",
                    left,
                    right
                )


            if op == TokenType.LESS_EQUAL:

                return self.builder.icmp_signed(
                    "<=",
                    left,
                    right
                )


            if op == TokenType.GREATER:

                return self.builder.icmp_signed(
                    ">",
                    left,
                    right
                )


            if op == TokenType.GREATER_EQUAL:

                return self.builder.icmp_signed(
                    ">=",
                    left,
                    right
                )



            # Logical

            if op == TokenType.AND:

                return self.builder.and_(
                    left,
                    right
                )


            if op == TokenType.OR:

                return self.builder.or_(
                    left,
                    right
                )

        
        if isinstance(node, FunctionCall):

            function = self.functions.get(
                node.name
            )


            if function is None:

                raise Exception(
                    f"Unknown function '{node.name}'"
                )


            arguments = []


            for argument in node.arguments:

                arguments.append(
                    self.generate_expression(
                        argument
                    )
                )


            return self.builder.call(
                function,
                arguments,
                name=f"{node.name}_call"
            )
            
        
        raise CodeGenerationError(
            "Unsupported AST node"
        )



    # ========================================================
    # Output
    # ========================================================

    def get_ir(self):
        """Return the generated LLVM IR as a string."""

        return str(self.module)