# EXORCISM LANG 

The written code is compiled into a cross-platform WebAssembly binary (.wasm), which runs natively via a tiny Node.js script.

## THE COMPILER

- compiler.py – The main entry point that orchestrates the complete compilation pipeline from source code to WebAssembly output.
- tokens.py – Defines all token types, language keywords, and token objects used by the lexer and parser.
- lexer.py – Converts raw source code into a stream of lexical tokens that the parser can understand.
- compiler_ast.py – Defines the Abstract Syntax Tree (AST) node classes that represent the structure of the source program.
- parser.py – Coordinates parsing by transforming the token stream into a complete AST using the parser modules.
- base.py – Provides the shared parser infrastructure, token navigation, and utility methods used by all parser components.
- expressions.py – Parses expressions, operators, literals, function calls, and mathematical precedence rules.
- statements.py – Parses executable statements such as declarations, assignments, print statements, and expression statements.
- controlflow.py – Parses control flow constructs including if, else, and nested statement blocks.
- symbols.py – Implements the symbol table for tracking variables, types, scopes, and identifier lookups.
- semantic.py – Performs semantic analysis, type checking, null-safety validation, and compile-time language rules.
- codegen.py – Traverses the AST and generates LLVM Intermediate Representation (IR) for WebAssembly compilation.
- build.py – Invokes LLVM/Clang to compile LLVM IR into a WebAssembly module and generates the JavaScript runtime launcher (run.js).

## HOW TO COMPILE & RUN - COMMANDS

### Clear the containing output dir
```console
del /f /q *.ll *.wasm run.js              
```

### Compile
```console
py compiler.py hello.lang 							 
```

### Run the executable program 
```console
build/node run.js 								 
```