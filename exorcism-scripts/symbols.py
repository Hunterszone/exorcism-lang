from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tokens import Token


class SymbolError(Exception):
    pass



# ============================================================
# Symbol Information
# ============================================================

@dataclass(slots=True)
class Symbol:

    name: str

    token: Token

    type_name: str

    nullable: bool

    initialized: bool = False



# ============================================================
# Scope
# ============================================================

class Scope:

    def __init__(self, parent: Optional["Scope"] = None):

        self.parent = parent

        self.symbols: dict[str, Symbol] = {}



    # --------------------------------------------------------
    # Define
    # --------------------------------------------------------

    def define(self, symbol: Symbol):

        if symbol.name in self.symbols:

            existing = self.symbols[symbol.name]

            raise SymbolError(
                f"Variable '{symbol.name}' already defined\n"
                f"First declaration: "
                f"{existing.token.line}:{existing.token.column}\n"
                f"Duplicate declaration: "
                f"{symbol.token.line}:{symbol.token.column}"
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



# ============================================================
# Symbol Table Manager
# ============================================================

class SymbolTable:


    def __init__(self):

        self.global_scope = Scope()

        self.current_scope = self.global_scope



    # ========================================================
    # Scope handling
    # ========================================================

    def enter_scope(self):

        self.current_scope = Scope(
            parent=self.current_scope
        )



    def exit_scope(self):

        if self.current_scope.parent is None:

            raise SymbolError(
                "Cannot exit global scope"
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
        type_name: str,
        nullable: bool,
        initialized: bool = False,
    ):

        symbol = Symbol(

            name=identifier.value,

            token=identifier,

            type_name=type_name,

            nullable=nullable,

            initialized=initialized,
        )


        self.current_scope.define(symbol)


        return symbol



    def resolve(
        self,
        identifier: Token
    ) -> Symbol:


        symbol = self.current_scope.lookup(
            identifier.value
        )


        if symbol is None:

            raise SymbolError(
                f"Unknown variable '{identifier.value}'\n"
                f"at {identifier.line}:"
                f"{identifier.column}"
            )


        return symbol



    def exists(
        self,
        name: str
    ) -> bool:

        return (
            self.current_scope.lookup(name)
            is not None
        )