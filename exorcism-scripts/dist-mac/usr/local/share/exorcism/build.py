from __future__ import annotations

import os
import shutil
import subprocess
import platform


class BuildError(Exception):
    """Raised when the WebAssembly build pipeline fails."""


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
        """Locate a usable clang installation for the WebAssembly build."""

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
        """Write LLVM IR to a file in the output directory."""

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
        """Build LLVM IR into a WebAssembly module."""


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
        """Create the JavaScript launcher for the generated WebAssembly file."""


        runner = os.path.join(
            self.output_dir,
            "run.js"
        )


        code = r'''
const fs = require("fs");
const path = require("path");


const wasmFile = path.join(
    __dirname,
    "hello.wasm"
);


const wasmBuffer = fs.readFileSync(
    wasmFile
);


let instance;


/*
 * Simple runtime heap.
 *
 * We start allocating at the end of the
 * currently allocated WebAssembly memory.
 *
 * This avoids interfering with the memory
 * already used by the generated program.
 */

let heapPointer = 0;


/*
 * Allocate memory inside WebAssembly memory.
 */

function allocate(size) {

    const memory =
        new Uint8Array(
            instance.exports.memory.buffer
        );


    /*
     * First allocation:
     * start at the current end of memory.
     */

    if (heapPointer === 0) {

        heapPointer = memory.byteLength;
    }


    const pointer = heapPointer;

    const requiredEnd =
        pointer + size;


    /*
     * WebAssembly memory grows in
     * 64 KiB pages.
     */

    const pageSize = 64 * 1024;


    if (requiredEnd > memory.byteLength) {

        const additionalBytes =
            requiredEnd - memory.byteLength;


        const additionalPages =
            Math.ceil(
                additionalBytes / pageSize
            );


        instance.exports.memory.grow(
            additionalPages
        );
    }


    heapPointer += size;


    return pointer;
}


/*
 * Concatenate two null-terminated strings.
 *
 * concat_strings(left, right) -> pointer
 */

function concatStrings(
    leftPtr,
    rightPtr
) {

    /*
     * Get the current WebAssembly memory.
     */
    let memory =
        new Uint8Array(
            instance.exports.memory.buffer
        );


    /*
     * Find the length of the first string.
     */
    let leftLength = 0;

    while (
        memory[leftPtr + leftLength] !== 0
    ) {

        leftLength++;
    }


    /*
     * Find the length of the second string.
     */
    let rightLength = 0;

    while (
        memory[rightPtr + rightLength] !== 0
    ) {

        rightLength++;
    }


    /*
     * Allocate enough space for:
     *
     * left string
     * + right string
     * + null terminator
     */
    const totalLength =
        leftLength +
        rightLength +
        1;


    const resultPtr =
        allocate(totalLength);


    /*
     * IMPORTANT:
     *
     * allocate() may have grown WebAssembly
     * memory, so the old Uint8Array is no
     * longer safe to use.
     *
     * Get a fresh view.
     */
    memory =
        new Uint8Array(
            instance.exports.memory.buffer
        );


    /*
     * Copy the first string.
     */
    for (
        let i = 0;
        i < leftLength;
        i++
    ) {

        memory[
            resultPtr + i
        ] = memory[
            leftPtr + i
        ];
    }


    /*
     * Copy the second string.
     */
    for (
        let i = 0;
        i < rightLength;
        i++
    ) {

        memory[
            resultPtr +
            leftLength +
            i
        ] = memory[
            rightPtr + i
        ];
    }


    /*
     * Null terminator.
     */
    memory[
        resultPtr +
        leftLength +
        rightLength
    ] = 0;


    return resultPtr;
}


/*
 * Convert an integer to a null-terminated string
 * stored inside WebAssembly memory.
 *
 * int_to_string(value) -> pointer
 */

function intToString(value) {

    const text =
        String(value);


    const encoded =
        new TextEncoder().encode(text);


    const resultPtr =
        allocate(encoded.length + 1);


    let memory =
        new Uint8Array(
            instance.exports.memory.buffer
        );


    for (
        let i = 0;
        i < encoded.length;
        i++
    ) {

        memory[
            resultPtr + i
        ] = encoded[i];
    }


    memory[
        resultPtr + encoded.length
    ] = 0;


    return resultPtr;
}


/*
 * Convert a float to a null-terminated string
 * stored inside WebAssembly memory.
 *
 * float_to_string(value) -> pointer
 */

function floatToString(value) {

    const text =
        String(value);


    const encoded =
        new TextEncoder().encode(text);


    const resultPtr =
        allocate(encoded.length + 1);


    let memory =
        new Uint8Array(
            instance.exports.memory.buffer
        );


    for (
        let i = 0;
        i < encoded.length;
        i++
    ) {

        memory[
            resultPtr + i
        ] = encoded[i];
    }


    memory[
        resultPtr + encoded.length
    ] = 0;


    return resultPtr;
}


/*
 * Convert a double to a null-terminated string
 * stored inside WebAssembly memory.
 *
 * double_to_string(value) -> pointer
 */

function doubleToString(value) {

    const text =
        String(value);


    const encoded =
        new TextEncoder().encode(text);


    const resultPtr =
        allocate(encoded.length + 1);


    let memory =
        new Uint8Array(
            instance.exports.memory.buffer
        );


    for (
        let i = 0;
        i < encoded.length;
        i++
    ) {

        memory[
            resultPtr + i
        ] = encoded[i];
    }


    memory[
        resultPtr + encoded.length
    ] = 0;


    return resultPtr;
}


WebAssembly.instantiate(
    wasmBuffer,
    {

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


                while (
                    memory[ptr] !== 0
                ) {

                    text += String.fromCharCode(
                        memory[ptr]
                    );


                    ptr++;
                }


                console.log(text);
            },


            concat_strings: (
                leftPtr,
                rightPtr
            ) => {

                return concatStrings(
                    leftPtr,
                    rightPtr
                );
            },


            int_to_string: (value) => {

                return intToString(value);
            },


            float_to_string: (value) => {

                return floatToString(value);
            },


            double_to_string: (value) => {

                return doubleToString(value);
            }
        }

    }
)
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
        """Compile LLVM IR and create its WebAssembly runner."""


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