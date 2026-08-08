import sys
import os

from compiler import Compiler
from build import WasmBuilder


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


def main():
    
    if len(sys.argv) >= 2 and sys.argv[1] in ("--version", "-v"): 
        
        exorcism_version = "0.1.0"
        
        print(f"Exorcism Language {exorcism_version}") 
        
        return
        
        
    if len(sys.argv) >= 2 and sys.argv[1] in ("--help", "-h"): 
        
        help_msg = '''
                    Exorcism Language Compiler

                    Usage:
                      exorcism <command> [options]

                    Commands:
                      build <file.exrc>       Compile an Exorcism source file to WebAssembly
                      run <file.exrc>         Compile and execute an Exorcism source file

                    Options:
                      -h, --help              Show this help message
                      -v, --version           Show the Exorcism version

                    Examples:
                      exorcism build hello.exrc
                      exorcism run hello.exrc
                      exorcism --version
                      exorcism --help
                '''
        
        print(help_msg) 
        
        return

    
    if len(sys.argv) < 3:

        print(
            "Usage:\n"
            "  exorcism build file.exrc\n"
            "  exorcism run file.exrc"
            "  exorcism --version"
        )

        return


    command = sys.argv[1]

    filename = sys.argv[2]
  

    if command == "build":

        build_command(
            filename

        )


    elif command == "run":

        run_command(
            filename
        )
        

    else:

        print(
            f"Unknown command '{command}'"
        )


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