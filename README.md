![alt text](https://github.com/Hunterszone/exorcism-lang/blob/main/exrc-mascot.png)

# I. The Exorcism Architecture

The Exorcism lang uses a modern compiler architecture with a **Python-based compiler frontend**, an **LLVM-powered backend**, 
and multiple output targets including **WebAssembly (`.wasm`)** and **intermediate representation (`.ll`)** files.

## The Compiler

                  EXORCISM LANGUAGE
                         │
                         ▼
                    SOURCE TEXT
                         │
                         ▼
                    ┌─────────┐
                    │  LEXER  │
                    └────┬────┘
                         │
                       Tokens
                         │
                         ▼
                    ┌─────────┐
                    │ PARSER  │
                    └────┬────┘
                         │
                        AST
                         │
                         ▼
				  Semantic Analyzer
                   │           │
                   ▼           ▼
               Symbol Table  Type System
                   │           │
                   └────┬──────┘
                        │
                        ▼
                   Validated AST
                        │
                        ▼
                ┌────────────────┐
                │ LLVM CODEGEN   │
                └───────┬────────┘
                        │
                     LLVM IR
                        │
                        ▼
                   LLVM / Clang
                        │
                      WASM
                        │
                        ▼
                     run.js
                        │
                        ▼
                     Node.js


### Python Frontend

The Exorcism compiler frontend is implemented in Python, handling:

- Lexical analysis
- Parsing
- AST generation
- Semantic analysis
- Type checking
- Symbol management

Why Python:

- Rapid iteration during language design
- Simple and readable compiler components
- Rich ecosystem for testing and tooling
- Easier experimentation with new language features

This allows Exorcism to evolve quickly while maintaining a clean compiler structure.

### LLVM Backend

The LLVM backend provides:

- Mature optimization passes
- Platform-independent code generation
- Efficient low-level representations
- A foundation used by many production languages


## The Runtime Environment

### No Exorcism VM
- Programs compile to native targets or WebAssembly
- Users don't need to install an Exorcism runtime

### Cross-platform compilation
The same lang distribution can target Windows, Linux, macOS, WebAssembly, and potentially more architectures through LLVM.

**NOTE**: The .js output file is required by the current execution model that uses JavaScript as the WebAssembly host/runtime launcher.
WebAssembly is a portable binary format, but it needs a host environment to:

- load the .wasm file
- provide imported functions
- provide memory access
- call exported functions


## The Exorcism CLI

**NOTE**: The Exorcism Setup Installer adds `exorcism.exe` to PATH, so that `.exrc` programs could be executed from any location.

```console
    Usage:
      exrc <command> [options]

    Commands:
      build <file.exrc>       Compile an Exorcism source file to WebAssembly
      run <file.exrc>         Compile and execute an Exorcism source file
	  doctor                  Do a toolchain/environment diagnostic & prerequisites check
	  analyze                 Does error diagnostics of the analyzed code block

    Options:
      -h, --help              Show this help message
      -v, --version           Show the Exorcism version

    Examples:
      exrc build hello.exrc
      exrc run hello.exrc
	  exrc analyze file.exrc
      exrc analyze file.exrc --json
	  exrc doctor
      exrc --version
      exrc --help						 
```

<br>

# II. The Exorcism Features & Tooling

## Compiler Features

- ✅ Strong type checking
- ✅ Compile-time null safety (`String? name = null;`)
- ✅ Automatic type inference (`var`)
- ✅ Mathematical operator precedence
- ✅ Cross-platform execution
- ✅ Syntax analysis & validation (`exrc analyze file.exrc`)
- 🛠️ Memory management - WIP


## Language Features

- ✅ Statically typed
- ✅ Function calls (`add(int a, int b);`)
- ✅ Function calls in expressions (`var x = add(int a, int b);`)
- ✅ Void functions
- ✅ Sequential conditional statements (`if-option-option-...else`)
- ✅ String concatenation
- 🛠️ User input handling - WIP
- 🛠️ Main entry point - WIP
- 🛠️ SWITCH-CASE statements - WIP
- 🛠️ Loops (`for`, `foreach`, `while`, `do-while`) - WIP
- 🛠️ Jump statements (`break`, `continue`) - WIP
- 🛠️ Logical operators (`AND`, `OR`) - WIP
- 🛠️ Coalesce operator (`isX?.isY`) - WIP
- 🛠️ Relational operator (`memberof`) - WIP
- 🛠️ Assignment operators (`= += -= *= /= %= &= ^= |= <<= >>= >>>=`) - WIP
- 🛠️ Bitwise operators (`XOR`, `BITSHIFT`) - WIP
- 🛠️ Lambda expressions (`() -> doSmth()`) - WIP
- 🛠️ OOP features (`classes, structs, interfaces`) - WIP
- 🛠️ OOP concepts (`abstraction/polymorphism/inheritance`) - WIP
- 🛠️ Generics support - WIP
- 🛠️ Access modifiers (`public`, `private`, etc.) - WIP
- 🛠️ Casting & ClassCastException - WIP
- 🛠️ Exception hierarchy - WIP
- 🛠️ Exception handling - WIP
- 🛠️ Data structures / Collections - WIP
- 🛠️ Getter/Setter API - WIP
- 🛠️ Async/Concurrency - WIP
- 🛠️ Standard library - WIP
- 🛠️ Unit testing - WIP


## Tooling

- ✅ Exorcism CLI (`exorcism.exe`)
- ✅ Perquisites checker (`exrc doctor`)
- ✅ Code analyzer (`exrc analyze`)
- 🛠️ Formatter (`exrc format`)
- 🛠️ Linter (`exrc lint`)
- 🛠️ Documentation generator (`exrc docs`)
- 🛠️ Package manager (`exrc install`)

<br>

# III. The Exorcism Language Syntax

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

## Function call expressions

Function call expressions are supported.

```exrc
print("Hello World");

int add(int a, int b)
{
    return a + b;
}

var x = add(10, 6);

print(12 + x);
```

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

<br>

# IV. What makes Exorcism awesome

## Simple but powerful language design

Many existing languages have accumulated decades of complexity, historical decisions, and compatibility requirements.

Exorcism aims to provide a clean language design with:

- strict typing
- explicit syntax
- predictable behavior
- simple compilation rules
- modern safety features

The goal is not to replace established languages, but to provide a focused environment where the language rules are easy to understand and reason about.

## Safer software development

Exorcism is designed with safety in mind.

Planned and implemented safety features include:

- semantic type checking
- null safety
- controlled memory access through WebAssembly
- explicit variable handling
- compile-time error detection

Errors should be discovered during compilation instead of causing unexpected runtime failures.


## Portable execution

By targeting WebAssembly, Exorcism programs can run in multiple environments:

- browsers
- Node.js
- WebAssembly runtimes
- embedded environments

---

💡A compiled Exorcism program is not tied to a single operating system or CPU architecture.


## Rich language features support

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

---

💡The compiler architecture is intentionally modular so new language features can be added without redesigning the entire system.

<br>

# V. The Exorcism VS Code Extension

Exorcism includes its own Visual Studio Code extension, providing a modern development experience with intelligent editing features for `.exrc` source files.

## Extension URL: 
https://marketplace.visualstudio.com/items?itemName=exorcism-dev.exorcism-lang


## Features

- ✅ Syntax highlighting
- ✅ Native support for `.exrc` files
- ✅ Real-time syntax validation
- ✅ Code auto-completion
- ✅ GOTO functions & variables definition
- ✅ Editor command menu for `.exrc` context
- ✅ Keywords documentation support
- ✅ Exorcism language icon and file association
- 🛠️ Automatic code corrections - WIP
- 🛠️ Smart code suggestions - WIP
- 🛠️ Language Server (IntelliSense) - WIP

---

💡The extension significantly improves developer productivity by reducing typing, detecting errors while writing code, and providing contextual suggestions for language keywords, functions, variables, and types.