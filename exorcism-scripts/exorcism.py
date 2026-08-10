import sys
import os
import shutil
import subprocess
import tempfile

from compiler import Compiler
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
    
    # Resolve source file independently of the
    # location of exorcism.exe.
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
            f"{source_file}:"
            f"{location.line}:"
            f"{location.column}: "
            f"{diagnostic.severity.value}: "
            f"{diagnostic.message}"
        )

    return 1 if diagnostics.has_errors else 0


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


def main():
    
    # No command

    if len(sys.argv) == 1:
        
        print(HELP_MSG)

        return 0
         
    
    command = sys.argv[1]
    
    
    # Version
    
    if len(sys.argv) >= 2 and sys.argv[1] in ("--version", "-v"): 
        
        print(f"Exorcism Language {EXORCISM_VERSION}") 
        
        return 0
        
    
    # Help
    
    if len(sys.argv) >= 2 and sys.argv[1] in ("--help", "-h"): 
        
        print(HELP_MSG) 
        
        return 0
    
    
    # Commands requiring a source file
    
    if command not in ("doctor", "--version", "-v") and len(sys.argv) < 3:
    
        print(HELP_MSG)

        return 1

   
    # Doctor
    
    if command == "doctor":

        return doctor_command()


    filename = sys.argv[2]
  

    # Build
    
    if command == "build":

        build_command(
            filename
        )


    # Run
    
    if command == "run":

        run_command(
            filename
        )
        
        
    source_file = sys.argv[2]
    
    
    # Analyze
    
    if command == "analyze":
        
        json_output = ( 
            len(sys.argv) >= 4 
            and sys.argv[3] == "--json" 
        ) 
        
        return analyze_command( 
            source_file, 
            json_output 
        )


    else:
        
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