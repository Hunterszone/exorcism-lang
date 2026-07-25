import enum
import os
import subprocess
from llvmlite import ir

# =====================================================================
# 1. LEXER (Lexical Analysis)
# =====================================================================
class TokenType(enum.Enum):
    TYPE = 1         # int, float, String
    IDENTIFIER = 2   # variable names
    ASSIGN = 3       # =
    INT_LITERAL = 4  # 42
    PLUS = 5         # +
    MINUS = 6        # -
    SEMICOLON = 7    # ;
    QUESTION = 8     # ? (For your Null Safety milestone)
    EOF = 9

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value
    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}')"

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0

    def get_next_token(self):
        while self.pos < len(self.text):
            current_char = self.text[self.pos]
            if current_char.isspace():
                self.pos += 1
                continue
            if current_char.isalpha():
                result = ""
                while self.pos < len(self.text) and self.text[self.pos].isalnum():
                    result += self.text[self.pos]
                    self.pos += 1
                if result in ["int", "float", "String"]:
                    return Token(TokenType.TYPE, result)
                return Token(TokenType.IDENTIFIER, result)
            if current_char.isdigit():
                result = ""
                while self.pos < len(self.text) and self.text[self.pos].isdigit():
                    result += self.text[self.pos]
                    self.pos += 1
                return Token(TokenType.INT_LITERAL, int(result))
            if current_char == '=':
                self.pos += 1
                return Token(TokenType.ASSIGN, '=')
            if current_char == '+':
                self.pos += 1
                return Token(TokenType.PLUS, '+')
            if current_char == '-':
                self.pos += 1
                return Token(TokenType.MINUS, '-')
            if current_char == ';':
                self.pos += 1
                return Token(TokenType.SEMICOLON, ';')
            if current_char == '?':
                self.pos += 1
                return Token(TokenType.QUESTION, '?')
            self.pos += 1
        return Token(TokenType.EOF, None)

# =====================================================================
# 2. AST DATA STRUCTURES & PARSER (Multi-Line Block Upgrade)
# =====================================================================
class ASTNode: pass

# UPGRADE: A core node designed to wrap sequential instructions together
class ProgramNode(ASTNode):
    def __init__(self, statements):
        self.statements = statements # List containing your sequential VarDeclNodes

class LiteralNode(ASTNode):
    def __init__(self, value):
        self.value = value

class BinOpNode(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class VarDeclNode(ASTNode):
    def __init__(self, var_type, is_nullable, name, expr_node):
        self.var_type = var_type
        self.is_nullable = is_nullable
        self.name = name
        self.expr_node = expr_node

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            raise Exception(f"Parser error: Expected token {token_type}, got {self.current_token.type}")

    def parse_primary(self):
        token = self.current_token
        if token.type == TokenType.INT_LITERAL:
            self.eat(TokenType.INT_LITERAL)
            return LiteralNode(token.value)
        raise Exception(f"Parser Error: Expected integer literal, got {token.type}")

    def parse_expression(self):
        node = self.parse_primary()
        while self.current_token.type in [TokenType.PLUS, TokenType.MINUS]:
            op_token = self.current_token
            self.eat(op_token.type)
            right_node = self.parse_primary()
            node = BinOpNode(node, op_token.value, right_node)
        return node

    def parse_declaration(self):
        type_token = self.current_token
        self.eat(TokenType.TYPE)
        
        is_nullable = False
        if self.current_token.type == TokenType.QUESTION:
            is_nullable = True
            self.eat(TokenType.QUESTION)
            
        id_token = self.current_token
        self.eat(TokenType.IDENTIFIER)
        
        self.eat(TokenType.ASSIGN)
        expr_node = self.parse_expression()
        self.eat(TokenType.SEMICOLON)
        
        return VarDeclNode(type_token.value, is_nullable, id_token.value, expr_node)

    # UPGRADE: Continuous parsing loop processing statements sequentially
    def parse_program(self):
        statements = []
        while self.current_token.type != TokenType.EOF:
            # Currently parses declarations sequentially; can be scaled to support loops or control flows later
            stmt = self.parse_declaration()
            statements.append(stmt)
        return ProgramNode(statements)

# =====================================================================
# 3. TYPE CHECKER (Multi-Line Variable Validation Pass)
# =====================================================================
class TypeChecker:
    def __init__(self):
        self.symbol_table = {}

    def check(self, node):
        # UPGRADE: Recurse through all program statements sequentially
        if isinstance(node, ProgramNode):
            for stmt in node.statements:
                self.check(stmt)
                
        elif isinstance(node, VarDeclNode):
            # Enforce strict compiler validation against declaring variables twice!
            if node.name in self.symbol_table:
                raise Exception(f"Strict Type Error: Variable '{node.name}' is already defined.")
                
            expr_type = self.get_expr_type(node.expr_node)
            if node.var_type != expr_type:
                raise Exception(f"Strict Type Mismatch: Cannot assign '{expr_type}' to '{node.var_type}'")
                
            # Cache layout tracking parameters
            self.symbol_table[node.name] = {"type": node.var_type, "nullable": node.is_nullable}
            print(f"[Type Checker] Verified: {node.var_type} {node.name}")

    def get_expr_type(self, node):
        if isinstance(node, LiteralNode):
            return "int"
        if isinstance(node, BinOpNode):
            left_type = self.get_expr_type(node.left)
            right_type = self.get_expr_type(node.right)
            if left_type == "int" and right_type == "int":
                return "int"
            raise Exception("Type Error: Math operations only supported on integers.")
        return "unknown"

# =====================================================================
# 4. CODE GENERATOR (LLVM IR Sequential Output Block Engine)
# =====================================================================
class LLVMGenerator:
    def __init__(self):
        self.module = ir.Module(name="javx_core_module")
        self.module.triple = "wasm32-unknown-unknown"
        
        print_type = ir.FunctionType(ir.VoidType(), [ir.IntType(32)])
        self.native_print = ir.Function(self.module, print_type, name="print_value_to_terminal")
        
        func_type = ir.FunctionType(ir.IntType(32), [])
        self.main_func = ir.Function(self.module, func_type, name="main")
        self.builder = ir.IRBuilder(self.main_func.append_basic_block(name="entry"))

    def generate_expr(self, node):
        if isinstance(node, LiteralNode):
            return ir.Constant(ir.IntType(32), node.value)
        if isinstance(node, BinOpNode):
            left_val = self.generate_expr(node.left)
            right_val = self.generate_expr(node.right)
            if node.op == '+':
                return self.builder.add(left_val, right_val, name="addtmp")
            if node.op == '-':
                return self.builder.sub(left_val, right_val, name="subtmp")
        raise Exception("Code Generation Error: Invalid expression architecture")

    def generate(self, node):
        # UPGRADE: Map each processed statement sequentially inside the LLVM builder environment
        if isinstance(node, ProgramNode):
            for stmt in node.statements:
                self.generate(stmt)
            # Safe final execution exit marker returning execution success status state code
            self.builder.ret(ir.Constant(ir.IntType(32), 0))
            
        elif isinstance(node, VarDeclNode):
            llvm_type = ir.IntType(32)
            ptr = self.builder.alloca(llvm_type, name=node.name)
            
            evaluated_value = self.generate_expr(node.expr_node)
            self.builder.store(evaluated_value, ptr)
            
            # Read and print each declaration output as it resolves sequentially
            loaded_val = self.builder.load(ptr, name="loaded")
            self.builder.call(self.native_print, [loaded_val])

    def get_ir_string(self):
        return str(self.module)

# =====================================================================
# 5. CROSS-PLATFORM SYSTEM COMPILER DRIVER
# =====================================================================
def compile_and_link_auto(llvm_ir_string):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_ll = os.path.join(script_dir, "output.ll")
    final_wasm = os.path.join(script_dir, "MyLanguageProgram.wasm")
    runner_js = os.path.join(script_dir, "run.js")

    with open(output_ll, "w") as f:
        f.write(llvm_ir_string)
    print(f"[*] Generated code mapped inside intermediate file: {output_ll}")

    clang_path = r"C:\Program Files\LLVM\bin\clang.exe"
    
    link_command = [
        clang_path, "-target", "wasm32-unknown-unknown", "-nostdlib",
        "-Wl,--no-entry", "-Wl,--export-all", "-Xlinker", "--allow-undefined",
        output_ll, "-o", final_wasm
    ]

    print("[*] Processing cross-platform compiler emission pass...")
    result = subprocess.run(link_command, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"🎉 SUCCESS! Universal core binary generated: {final_wasm}")
        
        js_code = (
            "const fs = require('fs');\n"
            "const path = require('path');\n"
            "const wasmFile = path.join(__dirname, 'MyLanguageProgram.wasm');\n"
            "const wasmBuffer = fs.readFileSync(wasmFile);\n\n"
            "WebAssembly.instantiate(wasmBuffer, {\n"
            "    env: { print_value_to_terminal: (val) => console.log(val) }\n"
            "}).then(obj => {\n"
            "    obj.instance.exports.main();\n"
            "}).catch(err => console.error(err));\n"
        )
        with open(runner_js, "w") as f:
            f.write(js_code)
        print(f"[*] Created automated launcher script: {runner_js}")
        print("\nExecute your language program using: node run.js")
    else:
        print("\n❌ Build Pipeline Error:")
        print(result.stderr)

# ROOT LEVEL EXECUTION BLOCK WITH SYNCED IDENTATION
if __name__ == "__main__":
    # MILESTONE: Multi-line, continuous, strictly typed code input block!
    source_code = "int firstVal = 10 + 5; int secondVal = 30 - 3;"
    
    print(f"Compiling Multi-Line Block:\n{source_code}\n")
    
    lexer = Lexer(source_code)
    parser = Parser(lexer)
    
    # Trigger the new multi-statement layout parsing algorithm entry pointer loop
    ast = parser.parse_program()
    
    # Process multi-statement type-checking verification passes
    type_checker = TypeChecker()
    type_checker.check(ast)
    
    codegen = LLVMGenerator()
    codegen.generate(ast)
    compile_and_link_auto(codegen.get_ir_string())