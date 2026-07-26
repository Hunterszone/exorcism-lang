import sys
import os

from compiler import Compiler
from build import WasmBuilder

class CompilerError(Exception):
    pass


def build_command(source_file):

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

    os.system(
        f"node {runner}"
    )


def main():

    if len(sys.argv) < 3:

        print(
            "Usage:\n"
            "  exorcism build file.exrc\n"
            "  exorcism run file.exrc"
        )

        return


    command = sys.argv[1]

    filename = sys.argv[2]


    if not filename.lower().endswith(".exrc"):

        print(
            "Error: Exorcism files must end with .exrc ❌"
        )

        return


    if not os.path.exists(filename):

        raise CompilerError(
            f"File not found: {filename}"
        )

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