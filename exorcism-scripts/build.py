from __future__ import annotations

import os
import shutil
import subprocess
import platform



class BuildError(Exception):
    pass



class WasmBuilder:
    """
    LLVM -> WebAssembly build pipeline.

    Requires:
        clang
        LLVM wasm target support
    """



    TARGET = "wasm32-unknown-unknown"



    def __init__(
        self,
        output_dir
    ):

        self.output_dir = os.path.abspath(
            output_dir
        )


        os.makedirs(
            self.output_dir,
            exist_ok=True
        )



    # ========================================================
    # Compiler discovery
    # ========================================================

    def find_clang(self):

        clang = shutil.which(
            "clang"
        )


        if clang:

            return clang



        system = platform.system()


        possible = []


        if system == "Windows":

            possible.extend([
                r"C:\Program Files\LLVM\bin\clang.exe",
                r"C:\LLVM\bin\clang.exe",
            ])


        elif system == "Linux":

            possible.extend([
                "/usr/bin/clang",
                "/usr/local/bin/clang",
            ])


        elif system == "Darwin":

            possible.extend([
                "/usr/bin/clang",
                "/opt/homebrew/bin/clang",
            ])



        for path in possible:

            if os.path.exists(path):

                return path



        raise BuildError(
            "clang compiler not found.\n"
            "Install LLVM and add clang to PATH."
        )



    # ========================================================
    # LLVM IR output
    # ========================================================

    def write_ir(
        self,
        llvm_ir: str,
        name="program"
    ):

        path = os.path.join(
            self.output_dir,
            f"{name}.ll"
        )
        

        with open(
            path,
            "w",
            encoding="utf8"
        ) as file:

            file.write(
                llvm_ir
            )


        return path



    # ========================================================
    # WebAssembly build
    # ========================================================

    def build_wasm(
        self,
        llvm_ir: str,
        name="program"
    ):


        clang = self.find_clang()


        ir_file = self.write_ir(
            llvm_ir,
            name
        )


        wasm_file = os.path.join(
            self.output_dir,
            f"{name}.wasm"
        )



        command = [

            clang,

            "-target",
            self.TARGET,

            "-nostdlib",

            "-Wl,--no-entry",

            "-Wl,--export-all",

            "-Wl,--allow-undefined",

            ir_file,

            "-o",

            wasm_file,
        ]


        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )


        if result.returncode != 0:

            raise BuildError(
                "LLVM build failed:\n\n"
                + result.stderr
            )


        return wasm_file


    # ========================================================
    # JavaScript launcher
    # ========================================================

    def create_runner(
        self,
        wasm_file
    ):


        runner = os.path.join(
            self.output_dir,
            "run.js"
        )


        code = r'''
const fs = require("fs");
const path = require("path");

const wasmFile = path.join(__dirname, "__WASM_FILE__");

const wasmBuffer = fs.readFileSync(wasmFile);

let instance;

WebAssembly.instantiate(wasmBuffer, {

    env: {

        print_int: (value) => {
            console.log(value);
        },
        
        print_string: (ptr) => {

            const memory =
                new Uint8Array(
                    instance.exports.memory.buffer
                );

            let text = "";

            while (memory[ptr] !== 0) {

                text += String.fromCharCode(
                    memory[ptr]
                );

                ptr++;
            }

            console.log(text);
        }
    }

})
.then(result => {

    instance = result.instance;

    instance.exports.main();

})
.catch(err => {

    console.error(err);

});
'''


        with open(
            runner,
            "w",
            encoding="utf8"
        ) as file:

            file.write(
                code.replace(
                    "__WASM_FILE__",
                    os.path.basename(wasm_file)
                )
            )


        return runner



    # ========================================================
    # Full pipeline
    # ========================================================

    def compile(
        self,
        llvm_ir,
        name="program"
    ):


        wasm = self.build_wasm(
            llvm_ir,
            name
        )


        runner = self.create_runner(
            wasm
        )


        return {
            "wasm": os.path.abspath(wasm),
            "runner": os.path.abspath(runner)
        }