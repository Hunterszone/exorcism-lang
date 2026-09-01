from __future__ import annotations

from dataclasses import dataclass

from abc import ABC


# ============================================================
# Base Type
# ============================================================

class TypeProperties(ABC):
    """Base class for all type definitions."""

    @property
    def name(self) -> str:
        """Return the type's name."""
        raise NotImplementedError()


    @property
    def nullable(self) -> bool:
        """Return whether the type accepts null values."""
        return False


    @property
    def is_reference(self) -> bool:
        """Return whether the type is a reference type."""
        return False


    @property
    def is_value(self) -> bool:
        """Return whether the type is a value type."""
        return False


    @property
    def is_numeric(self) -> bool:
        """Return whether the type represents a numeric value."""
        return False


    @property
    def is_primitive(self) -> bool:
        """Return whether the type is a primitive type."""
        return False


    def make_nullable(self) -> TypeProperties:
        """Return this type as a nullable type."""

        if self.nullable:
            return self

        return NullableType(self)


    def __str__(self):

        return self.name



# ============================================================
# Primitive Types
# ============================================================

@dataclass(frozen=True)
class PrimitiveType(TypeProperties):
    """Represents a primitive type in the Exorcism language."""

    primitive_name: str


    @property
    def name(self):

        return self.primitive_name


    @property
    def is_value(self):

        return True


    @property
    def is_primitive(self):

        return True


    @property
    def is_numeric(self):

        return self.primitive_name in {

            "int",
            "float",
            "double"
        }



# ============================================================
# Class Types
# ============================================================

@dataclass(frozen=True)
class ClassType(TypeProperties):
    """Represent a class type."""

    class_name: str


    @property
    def name(self):

        return self.class_name


    @property
    def is_reference(self):

        return True



# ============================================================
# Interface Types
# ============================================================

@dataclass(frozen=True)
class InterfaceType(TypeProperties):
    """Represent an interface type."""

    interface_name: str


    @property
    def name(self):

        return self.interface_name


    @property
    def is_reference(self):

        return True



# ============================================================
# Array Types
# ============================================================

@dataclass(frozen=True)
class ArrayType(TypeProperties):
    """Represent an array type with an element type."""

    element_type: TypeProperties


    @property
    def name(self):

        return f"{self.element_type.name}[]"


    @property
    def is_reference(self):

        return True



# ============================================================
# Function Types
# ============================================================

@dataclass(frozen=True)
class FunctionType(TypeProperties):
    """Represent a function type with parameter and return types."""

    parameters: tuple[TypeProperties, ...]

    return_type: TypeProperties


    @property
    def name(self):

        params = ", ".join(
            str(x)
            for x in self.parameters
        )

        return (
            f"({params}) -> "
            f"{self.return_type}"
        )



# ============================================================
# Generic Types
# ============================================================

@dataclass(frozen=True)
class GenericParameter(TypeProperties):
    """A named type parameter used by a generic type."""

    parameter_name: str


    @property
    def name(self):

        return self.parameter_name



@dataclass(frozen=True)
class GenericInstanceType(TypeProperties):
    """A generic type instantiated with concrete type arguments."""

    base_type: TypeProperties

    arguments: tuple[TypeProperties, ...]


    @property
    def name(self):

        args = ", ".join(
            str(x)
            for x in self.arguments
        )

        return (
            f"{self.base_type.name}"
            f"<{args}>"
        )



# ============================================================
# Nullable Types
# ============================================================

@dataclass(frozen=True)
class NullableType(TypeProperties):
    """A type that permits a null value."""

    base_type: TypeProperties


    @property
    def name(self):

        return f"{self.base_type.name}?"


    @property
    def nullable(self):

        return True


    @property
    def is_reference(self):

        return self.base_type.is_reference


    @property
    def is_value(self):

        return self.base_type.is_value



# ============================================================
# Null Literal Type
# ============================================================

class NullType(TypeProperties):

    @property
    def name(self):

        return "null"



# ============================================================
# Built-in Types
# ============================================================

INT = PrimitiveType("int")

FLOAT = PrimitiveType("float")

DOUBLE = PrimitiveType("double")

BOOL = PrimitiveType("bool")

CHAR = PrimitiveType("char")

VOID = PrimitiveType("void")

STRING = ClassType("String")

OBJECT = ClassType("Object")

NULL = NullType()



# ============================================================
# Builtin registry
# ============================================================

BUILTIN_TYPES = {

    # primitive types

    "int": INT,
    "float": FLOAT,
    "double": DOUBLE,
    "bool": BOOL,
    "char": CHAR,
    "void": VOID,


    # reference types
    
    "String": STRING,
    "Object": OBJECT
}


def resolve_builtin_type(
    name: str
):
    """Return the built-in type registered under ``name``."""

    return BUILTIN_TYPES.get(name)