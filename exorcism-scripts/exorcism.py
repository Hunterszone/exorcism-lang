import sys
import os
import shutil
import subprocess
import tempfile
import json

from compiler import Compiler
from symbols import FunctionSymbol
from build import WasmBuilder, BuildError

# Force UTF-8 output on Windows
if sys.platform == "win32":
    try: 
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

EXORCISM_VERSION = "0.1.0"
HELP_MSG = '''
    Usage:
      exorcism <command> [options]

    Commands:
      build <file.exrc>       Compiles an Exorcism source file to WebAssembly
      run <file.exrc>         Compiles and execute an Exorcism source file
      doctor                  Does a toolchain/environment diagnostics & prerequisites check
      analyze                 Does error diagnostics of the analyzed code block

    Options:
      -h, --help              Show this help message
      -v, --version           Show the Exorcism version

    Examples:
      exorcism build hello.exrc
      exorcism run hello.exrc
      exorcism analyze file.exrc
      exorcism analyze file.exrc --json
      exorcism doctor
      exorcism --version
      exorcism --help		
'''
  
# ========================================================
# Build Command
# ========================================================

def build_command(source_file):
    """Compile an Exorcism source file to a WASM artifact and runner."""

    source_file = os.path.abspath(
        source_file
    )

    compiler = Compiler()

    result = compiler.compile_file(
        source_file
    )
    
    print()
    
    print(
        "BUILD SUCCEEDED! ✅"
    )

    print(
        f"WASM: {result['wasm']}"
    )

    print(
        f"Runner: {result['runner']}"
    )

    return result


# ========================================================
# Run Command
# ========================================================

def run_command(source_file):
    """Build the source file and execute the generated runner with Node."""

    result = build_command(
        source_file
    )

    runner = result["runner"]

    print("\nOutput: ")
    
    process = subprocess.run(
        [
            "node",
            runner
        ]
    )
    
    # Propagate Node's exit code.
    if process.returncode != 0:
        sys.exit(
            process.returncode
        )


# ========================================================
# Doctor Command
# ========================================================
        
def doctor_command():
    """Display Exorcism environment information."""

    print("Exorcism environment")
    print()

    # ---------------------------------
    # Exorcism compiler
    # ---------------------------------

    print(
        f"✓ Exorcism compiler: {EXORCISM_VERSION}"
    )


    # ---------------------------------
    # Python frontend
    # ---------------------------------

    if getattr(sys, "frozen", False):

        print(
            "✓ Python frontend: bundled"
        )

    else:

        print(
            "✓ Python frontend: source"
        )


    # ---------------------------------
    # LLVM / Clang
    # ---------------------------------

    with tempfile.TemporaryDirectory() as temp_dir:

        builder = WasmBuilder(
            output_dir=temp_dir
        )

        try:

            clang = builder.find_clang()

            print(
                "✓ LLVM/Clang: found"
            )

        except BuildError:

            print(
                "✗ LLVM/Clang: not found"
            )

            clang = None


    # ---------------------------------
    # Node.js
    # ---------------------------------

    node = shutil.which(
        "node"
    )

    if node:

        print(
            "✓ Node.js: found"
        )

    else:

        print(
            "✗ Node.js: not found"
        )


    # ---------------------------------
    # WebAssembly target
    # ---------------------------------

    wasm_available = False

    if clang:

        try:

            result = subprocess.run(
                [
                    clang,
                    "--print-targets"
                ],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:

                targets = result.stdout.lower()

                wasm_available = (
                    "wasm32" in targets
                )

        except Exception:

            wasm_available = False


    if wasm_available:

        print(
            "✓ WebAssembly target: available"
        )

    else:

        print(
            "✗ WebAssembly target: unavailable"
        )


    print()


    if (
        clang
        and node
        and wasm_available
    ):

        print(
            "Environment is ready."
        )

        return 0


    print(
        "Environment is not ready."
    )

    return 1


# ========================================================
# Analyze Command
# ========================================================

def analyze_command(
    source_file,
    json_output=False
):
    """Analyze a source file and report diagnostics."""

    compiler = Compiler()


    diagnostics = compiler.analyze_file(
        source_file
    )
    

    if json_output:

        print(
            diagnostics.to_json()
        )

        return 1 if diagnostics.has_errors else 0


    if diagnostics.is_empty:

        print(
            "No errors found."
        )

        return 0


    for diagnostic in diagnostics.diagnostics:

        location = diagnostic.location

        print(
            f"{location.line}:"
            f"{location.column}: "
            f"{diagnostic.severity.value}: "
            f"{diagnostic.message}"
        )


    return 1 if diagnostics.has_errors else 0
    

# ========================================================
# Analyze STDIN Command
# ========================================================

def analyze_stdin_command(
    json_output=False
):
    """Analyze source code from STDIN and report diagnostics."""

    source = sys.stdin.read()


    compiler = Compiler()


    diagnostics = compiler.analyze_source(
        source
    )


    if json_output:

        print(
            diagnostics.to_json()
        )

        return 1 if diagnostics.has_errors else 0


    if diagnostics.is_empty:

        print(
            "No errors found."
        )

        return 0


    for diagnostic in diagnostics.diagnostics:

        location = diagnostic.location

        print(
            f"{location.line}:"
            f"{location.column}: "
            f"{diagnostic.severity.value}: "
            f"{diagnostic.message}"
        )


    return 1 if diagnostics.has_errors else 0


# ========================================================
# Symbol to Json
# ========================================================

def symbol_to_json(symbol):
    """Convert a symbol into a JSON-serializable dictionary."""


    result = {
        "name": symbol.name,
        "kind": (
            "function"
            if isinstance(symbol, FunctionSymbol)
            else "variable"
        ),
        "type": str(symbol.type),
        "line": symbol.token.line,
        "column": symbol.token.column,
    }


    if isinstance(symbol, FunctionSymbol):
        result["returnType"] = str(symbol.return_type)

        result["parameters"] = [
            {
                "name": parameter.name,
                "type": str(parameter.parameter_type),
            }
            for parameter in symbol.parameters
        ]

    
    return result
    
    
# ========================================================
# Symbols command function
# ========================================================
    
def symbols_command(source_file):
    """Extract and print symbol information from a source file."""

    
    with open(
        source_file,
        "r",
        encoding="utf-8",
    ) as file:
        source = file.read()


    compiler = Compiler()


    symbol_table = compiler.analyze_symbols(
        source
    )


    symbols = [
        symbol_to_json(symbol)
        for symbol in symbol_table.all_symbols()
    ]


    print(
        json.dumps(
            {"symbols": symbols},
            indent=4,
        )
    )


    return 0
    

# ========================================================
# Main function
# ========================================================

def main():
    """Main entry point for the Exorcism command-line tool."""

    # ========================================================
    # No command
    # ========================================================

    if len(sys.argv) == 1:

        print(
            HELP_MSG
        )

        return 0


    command = sys.argv[1]


    # ========================================================
    # Version
    # ========================================================

    if command in (
        "--version",
        "-v"
    ):

        print(
            f"Exorcism Language {EXORCISM_VERSION}"
        )

        return 0


    # ========================================================
    # Help
    # ========================================================

    if command in (
        "--help",
        "-h"
    ):

        print(
            HELP_MSG
        )

        return 0


    # ========================================================
    # Doctor
    # ========================================================

    if command == "doctor":

        return doctor_command()


    # ========================================================
    # Build
    # ========================================================

    if command == "build":

        if len(sys.argv) < 3:

            print(
                HELP_MSG
            )

            return 1

        filename = sys.argv[2]

        build_command(
            filename
        )

        return 0


    # ========================================================
    # Run
    # ========================================================

    if command == "run":

        if len(sys.argv) < 3:

            print(
                HELP_MSG
            )

            return 1

        filename = sys.argv[2]

        run_command(
            filename
        )

        return 0


    # ========================================================
    # Symbols
    # ========================================================
    
    if command == "symbols":
        
        if len(sys.argv) < 3:
            
            print(
                HELP_MSG
            )
            
            return 1

        
        filename = sys.argv[2]

        
        return symbols_command(
            filename
        )
        
        
    # ========================================================
    # Analyze
    # ========================================================

    if command == "analyze":

        if len(sys.argv) < 3:

            print(
                HELP_MSG
            )

            return 1


        # ---------------------------------
        # Analyze current unsaved source
        # from stdin
        # ---------------------------------

        if sys.argv[2] == "--stdin":

            json_output = (
                len(sys.argv) >= 4
                and sys.argv[3] == "--json"
            )

            return analyze_stdin_command(
                json_output
            )


        # ---------------------------------
        # Analyze source file
        # ---------------------------------

        source_file = sys.argv[2]

        json_output = (
            len(sys.argv) >= 4
            and sys.argv[3] == "--json"
        )

        return analyze_command(
            source_file,
            json_output
        )


    # ========================================================
    # Unknown command
    # ========================================================

    print(
        f"Unknown command '{command}'"
    )

    return 1


if __name__ == "__main__":

    try:
        main()

    except Exception as e:

        print(
            "COMPILATION ERROR ❌"
        )

        print(
            e
        )

        sys.exit(1)