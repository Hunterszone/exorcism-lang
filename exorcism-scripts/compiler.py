from __future__ import annotations

import sys
import os

from parser import Parser
from lexer import Lexer, LexerError
from diagnostics import DiagnosticBag
from semantic import SemanticAnalyzer, SemanticError
from symbols import SymbolError
from base import ParserError

from codegen import (
    LLVMCodeGenerator,
    CodeGenerationError
)

from build import (
    WasmBuilder,
    BuildError
)


if sys.platform == "win32": 
    try: 
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8") 
    except AttributeError: 
        pass


class CompilerError(Exception):
    """Exception raised for compiler errors."""

    def __init__(
        self,
        message,
        token=None,
        related_token=None
    ):

        super().__init__(message)

        self.message = message
        self.token = token
        self.related_token = related_token



class Compiler:
    """
    Complete WORM compiler pipeline.

    WORM:

        Write
        Optimize
        Run
        Machine-code(WebAssembly)

    """


    def __init__(self):

        pass



    # ========================================================
    # Compile source text
    # ========================================================

    def compile_source(
        self,
        source: str,
        output="program"
    ):


        try:

            print("[1/5] Lexing...")


            lexer = Lexer(
                source
            )


            tokens = lexer.tokenize()


            # FOR DEBUGGING
            #for token in tokens:
            #    print(token)

            print("[2/5] Parsing...")


            parser = Parser(
                tokens
            )


            ast = parser.parse()



            print("[3/5] Semantic analysis...")


            analyzer = SemanticAnalyzer()

            analyzer.analyze(
                ast
            )



            print("[4/5] Generating LLVM IR...")


            generator = LLVMCodeGenerator()


            module = generator.generate(
                ast
            )


            llvm_ir = str(
                module
            )



            print("[5/5] Building WebAssembly...")

            output_dir = os.path.dirname(
                output
            )

            builder = WasmBuilder(
                output_dir=output_dir
            )

            result = builder.compile(
                llvm_ir,
                os.path.basename(output)
            )

            return result

        except (
            ParserError,
            SemanticError,
            CodeGenerationError,
            BuildError
        ) as error:

            raise CompilerError(
                str(error),
                token=getattr(
                    error,
                    "token",
                    None
                ),
                related_token=getattr(
                    error,
                    "related_token",
                    None
                )
            ) from error



    # ========================================================
    # Compile file
    # ========================================================

    def compile_file(
        self,
        filename,
        output=None
    ):
        """Compile a single .exrc file to bytecode."""

        filename = os.path.abspath(
            filename
        )


        if not os.path.exists(filename):

            raise CompilerError(
                f"File not found: {filename}"
            )


        if not filename.lower().endswith(".exrc"):

            raise Exception(
                f"Invalid source file extension: '{filename}'. "
                "Expected .exrc"
            )


        with open(
            filename,
            "r",
            encoding="utf8"
        ) as file:

            source = file.read()


        source_dir = os.path.dirname(
            filename
        )

        name = os.path.splitext(
            os.path.basename(filename)
        )[0]

        
        # ---------------------------------
        # Generated artifacts
        # ---------------------------------

        artifacts_dir = os.path.join(
            source_dir,
            "artifacts"
        )


        os.makedirs(
            artifacts_dir,
            exist_ok=True
        )

        
        if output is None:

            output = os.path.join(
                artifacts_dir,
                name
            )


        return self.compile_source(
            source,
            output=output
        )    
        
    
    # ========================================================
    # Analyze source
    # ========================================================
    
    def analyze_source(
        self,
        source: str
    ):
        """Analyze source code and perform semantic analysis."""

        diagnostics = DiagnosticBag()


        def add_error(
            error,
            default_line=1,
            default_column=1
        ):

            token = getattr(
                error,
                "token",
                None
            )


            if token is not None:

                line = token.line
                column = token.column

            else:

                line = getattr(
                    error,
                    "line",
                    default_line
                )

                column = getattr(
                    error,
                    "column",
                    default_column
                )


            diagnostics.error(
                message=getattr(
                    error,
                    "message",
                    str(error)
                ),

                line=line,

                column=column,

                length=1,
            )


        try:

            lexer = Lexer(
                source
            )

            tokens = lexer.tokenize()


            parser = Parser(
                tokens
            )

            ast = parser.parse()


            analyzer = SemanticAnalyzer()

            analyzer.analyze(
                ast
            )


        except LexerError as error:

            add_error(
                error
            )


        except ParserError as error:

            add_error(
                error
            )


        except SemanticError as error:

            add_error(
                error
            )


        except SymbolError as error:

            add_error(
                error
            )


        except Exception as error:

            diagnostics.error(
                message=str(error),
                line=1,
                column=1,
                length=1,
            )


        return diagnostics


    # ========================================================
    # Analyze source & file
    # ========================================================

    def analyze_file(
        self,
        filename
    ):
        """Analyze a source file and return diagnostics."""
        filename = os.path.abspath(
            filename
        )

        if not os.path.exists(filename):

            raise CompilerError(
                f"File not found: {filename}"
            )

        if not filename.lower().endswith(".exrc"):

            raise CompilerError(
                f"Invalid source file extension: '{filename}'. "
                "Expected .exrc"
            )

        with open(
            filename,
            "r",
            encoding="utf8"
        ) as file:

            source = file.read()

        return self.analyze_source(
            source
        )
        
        
    def analyze_symbols(
        self,
        source: str
    ):

        lexer = Lexer(
            source
        )

        tokens = lexer.tokenize()


        parser = Parser(
            tokens
        )

        ast = parser.parse()


        analyzer = SemanticAnalyzer()

        analyzer.analyze(
            ast
        )

        
        return analyzer.symbols