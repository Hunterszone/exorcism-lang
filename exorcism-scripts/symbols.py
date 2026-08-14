from __future__ import annotations

from dataclasses import dataclass, field

from typing import Optional

from tokens import Token

from exorcism_types import Type, VOID

from type_system import TypeSystem

class SymbolError(Exception):

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



# ============================================================
# Symbol Information
# ============================================================

@dataclass(slots=True)
class Symbol:

    name: str

    token: Token

    type: Type

    initialized: bool = False


@dataclass(slots=True)
class FunctionSymbol(Symbol):
    
    parameters: list["Symbol"] = field(
        default_factory=list
    )

    return_type: Type = VOID


# ============================================================
# Scope
# ============================================================

class Scope:

    def __init__(
        self,
        parent: Optional["Scope"] = None,
        start_line: int = 0,
        start_column: int = 0,
    ):

        self.parent = parent

        self.symbols: dict[str, Symbol] = {}

        # ----------------------------------------------------
        # Retained child scopes
        # ----------------------------------------------------

        self.children: list["Scope"] = []

        # ----------------------------------------------------
        # Source range
        # ----------------------------------------------------

        self.start_line = start_line
        self.start_column = start_column

        self.end_line = 0
        self.end_column = 0


    # --------------------------------------------------------
    # Define
    # --------------------------------------------------------

    def define(self, symbol: Symbol):

        if symbol.name in self.symbols:

            existing = self.symbols[symbol.name]

            raise SymbolError(
                f"Variable '{symbol.name}' already defined",
                token=symbol.token,
                related_token=existing.token
            )

        self.symbols[symbol.name] = symbol


    # --------------------------------------------------------
    # Lookup current scope
    # --------------------------------------------------------

    def lookup_local(self, name: str):

        return self.symbols.get(name)


    # --------------------------------------------------------
    # Lookup all scopes
    # --------------------------------------------------------

    def lookup(self, name: str):

        if name in self.symbols:

            return self.symbols[name]

        if self.parent:

            return self.parent.lookup(name)

        return None


    # --------------------------------------------------------
    # Visible symbols
    # --------------------------------------------------------

    def visible_symbols(self):

        visible = {}

        scope = self

        while scope is not None:

            for name, symbol in scope.symbols.items():

                # Keep the nearest definition.
                # This automatically handles shadowing.
                if name not in visible:
                    visible[name] = symbol

            scope = scope.parent

        return list(visible.values())


    # --------------------------------------------------------
    # All symbols in current scope
    # --------------------------------------------------------

    def all_symbols(self):

        return list(
            self.symbols.values()
        )


    # --------------------------------------------------------
    # Source position
    # --------------------------------------------------------

    def contains_position(
        self,
        line: int,
        column: int,
    ):

        start = (
            self.start_line,
            self.start_column,
        )

        end = (
            self.end_line,
            self.end_column,
        )

        position = (
            line,
            column,
        )

        return start <= position <= end


# ============================================================
# Symbol Table Manager
# ============================================================

class SymbolTable:

    def __init__(self):

        self.global_scope = Scope()

        self.current_scope = (
            self.global_scope
        )


    # ========================================================
    # Scope handling
    # ========================================================

    def enter_scope(
        self,
        start_line: int = 0,
        start_column: int = 0,
    ):

        parent = self.current_scope

        new_scope = Scope(
            parent=parent,
            start_line=start_line,
            start_column=start_column,
        )

        # Retain the scope in the scope tree.
        parent.children.append(
            new_scope
        )

        self.current_scope = new_scope

        return new_scope


    def exit_scope(
        self,
        end_line: int = 0,
        end_column: int = 0,
    ):

        if self.current_scope.parent is None:

            raise SymbolError(
                "Cannot exit global scope"
            )

        # Store the source range before
        # leaving the scope.
        self.current_scope.end_line = (
            end_line
        )

        self.current_scope.end_column = (
            end_column
        )

        self.current_scope = (
            self.current_scope.parent
        )


    # ========================================================
    # Variables
    # ========================================================

    def declare(
        self,
        identifier: Token,
        type: Type,
        initialized: bool = False,
    ):

        symbol = Symbol(

            name=identifier.value,

            token=identifier,

            type=type,

            initialized=initialized,
        )

        self.current_scope.define(
            symbol
        )

        return symbol


    # ========================================================
    # Resolve
    # ========================================================

    def resolve(
        self,
        identifier: Token
    ) -> Symbol:

        symbol = self.current_scope.lookup(
            identifier.value
        )

        if symbol is None:

            raise SymbolError(
                f"Unknown variable "
                f"'{identifier.value}'",
                identifier
            )

        return symbol


    # ========================================================
    # Lookup by name
    # ========================================================

    def lookup_name(
        self,
        name: str
    ):

        return self.current_scope.lookup(
            name
        )


    # ========================================================
    # Exists
    # ========================================================

    def exists(
        self,
        name: str
    ) -> bool:

        return (
            self.current_scope.lookup(name)
            is not None
        )


    # ========================================================
    # Current scope
    # ========================================================

    def current(self):

        return self.current_scope


    # ========================================================
    # Visible symbols
    # ========================================================

    def visible_symbols(self):

        return self.current_scope.visible_symbols()


    # ========================================================
    # All symbols
    # ========================================================

    def all_symbols(self):

        return self.global_scope.all_symbols()


    # ========================================================
    # All scopes
    # ========================================================

    def all_scopes(self):

        scopes = []

        def visit(scope):

            scopes.append(
                scope
            )

            for child in scope.children:

                visit(child)

        visit(
            self.global_scope
        )

        return scopes


    # ========================================================
    # Scope at source position
    # ========================================================

    def scope_at(
        self,
        line: int,
        column: int,
    ):

        def find_scope(scope):

            if not scope.contains_position(
                line,
                column,
            ):
                return None

            for child in scope.children:

                result = find_scope(
                    child
                )

                if result is not None:
                    return result

            return scope

        return find_scope(
            self.global_scope
        )