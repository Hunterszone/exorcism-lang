# Exorcism Language Overview 

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

### Build
```console
exorcism build hello.exrc						 
```

### Build & Run
```console
exorcism run hello.exrc						 
```

# Exorcism Language Syntax

Exorcism is a statically typed, compiled programming language targeting **WebAssembly** through **LLVM**. Its syntax is intentionally simple while providing modern language features such as strict typing, compile-time null safety, type inference, and structured control flow.

---

## Variable Declarations

Variables can be declared using explicit types or automatic type inference.

```exrc
int age = 25;

float price = 12.50;

String name = "John";

var score = 100;
```

---

## Nullable Types

Types followed by `?` may contain `null`.

```exrc
String? nickname = null;

int? value = null;
```

Assigning `null` to a non-nullable variable results in a compile-time error.

```exrc
int number = null;     // Compile Error
```

---

## Type Inference

The `var` keyword automatically infers the variable type from its initializer.

```exrc
var count = 10;          // int

var message = "Hello";   // String
```

Once inferred, the variable remains strongly typed.

---

## Primitive Types

Current primitive types include:

| Type | Description |
|------|-------------|
| `int` | 32-bit signed integer |
| `float` | Floating-point number |
| `String` | UTF-8 string |
| `bool` | Boolean (`true` / `false`) |

---

## Arithmetic Expressions

Operator precedence follows standard mathematical rules.

```exrc
int result = 2 + 5 * 8;
```

Equivalent to:

```text
2 + (5 * 8)
```

Supported operators:

| Operator | Meaning |
|----------|---------|
| `+` | Addition |
| `-` | Subtraction |
| `*` | Multiplication |
| `/` | Division |

Expressions may be nested.

```exrc
int value = (10 + 5) * (8 - 2);
```

---

## Assignments

Variables may be reassigned after declaration.

```exrc
int count = 5;

count = count + 1;
```

---

## String Literals

Strings are enclosed using double quotes.

```exrc
String text = "Hello World!";
```

---

## Boolean Literals

```exrc
bool enabled = true;

bool disabled = false;
```

---

## Null Literal

```exrc
String? name = null;
```

---

## If / Else Statements

Conditional execution is supported.

```exrc
int age = 20;

if (age >= 18)
{
    print("Adult");
}
else
{
    print("Minor");
}
```

Nested conditionals are also supported.

```exrc
if (x > 10)
{
    if (y == 5)
    {
        print("Nested");
    }
}
```

---

## Comparison Operators

Supported comparison operators include:

| Operator | Meaning |
|----------|---------|
| `==` | Equal |
| `!=` | Not equal |
| `>` | Greater than |
| `<` | Less than |
| `>=` | Greater than or equal |
| `<=` | Less than or equal |

Example:

```exrc
if (score >= 90)
{
    print("Excellent");
}
```

---

## Printing

The standard library provides a built-in `print()` function.

```exrc
print("Hello World!");
```

Printing variables:

```exrc
int score = 100;

print(score);
```

---

## Comments

Single-line comments:

```exrc
// This is a comment
```

Multi-line comments:

```exrc
/*
   Multiple
   line
   comment
*/
```

---

## Example Program

```exrc
String message = "Hello World!";

int a = 5;
int b = 10;

var result = a + b * 2;

if (result > 20)
{
    print(message);
}
else
{
    print("Computation failed");
}
```

---

## Language Characteristics

- ✅ Statically typed
- ✅ Strong type checking
- ✅ Compile-time null safety
- ✅ Automatic type inference (`var`)
- ✅ Mathematical operator precedence
- ✅ LLVM Intermediate Representation (IR) generation
- ✅ WebAssembly compilation
- ✅ JavaScript runtime launcher generation
- ✅ Cross-platform execution

---

## File Extension

Exorcism source files use the `.exrc` extension.

Example:

```text
hello.exrc
calculator.exrc
game.exrc
```

The compiler produces:

```text
build/
├── hello.wasm
├── run.js
└── program.ll
```

# What problems does Exorcism solve ?

## 1. A simple but powerful language design

Many existing languages have accumulated decades of complexity, historical decisions, and compatibility requirements.

Exorcism aims to provide a clean language design with:

- strict typing
- explicit syntax
- predictable behavior
- simple compilation rules
- modern safety features

The goal is not to replace established languages, but to provide a focused environment where the language rules are easy to understand and reason about.

---

## 2. Safer software development

Exorcism is designed with safety in mind.

Planned and implemented safety features include:

- semantic type checking
- null safety
- controlled memory access through WebAssembly
- explicit variable handling
- compile-time error detection

Errors should be discovered during compilation instead of causing unexpected runtime failures.

---

## 3. Portable execution

By targeting WebAssembly, Exorcism programs can run in multiple environments:

- browsers
- Node.js
- WebAssembly runtimes
- embedded environments

A compiled Exorcism program is not tied to a single operating system or CPU architecture.

---

## 4. A foundation for experimenting with programming language features

Exorcism provides a platform for exploring advanced language concepts, including:

- functions
- recursion
- control flow
- arrays
- structures
- pattern matching
- type inference
- memory management
- optimization techniques

The compiler architecture is intentionally modular so new language features can be added without redesigning the entire system.

---