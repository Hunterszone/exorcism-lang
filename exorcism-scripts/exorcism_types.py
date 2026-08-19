from __future__ import annotations

from dataclasses import dataclass
from abc import ABC


# ============================================================
# Base Type
# ============================================================

class Type(ABC):
    """Base class for all type definitions."""

    @property
    def name(self) -> str:
        raise NotImplementedError()


    @property
    def nullable(self) -> bool:
        return False


    @property
    def is_reference(self) -> bool:
        return False


    @property
    def is_value(self) -> bool:
        return False


    @property
    def is_numeric(self) -> bool:
        return False


    @property
    def is_primitive(self) -> bool:
        return False


    def make_nullable(self) -> Type:

        if self.nullable:
            return self

        return NullableType(self)


    def __str__(self):

        return self.name



# ============================================================
# Primitive Types
# ============================================================

@dataclass(frozen=True)
class PrimitiveType(Type):
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
class ClassType(Type):
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
class InterfaceType(Type):
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
class ArrayType(Type):
    """Represent an array type with an element type."""

    element_type: Type


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
class FunctionType(Type):
    """Represent a function type with parameter and return types."""

    parameters: tuple[Type, ...]

    return_type: Type


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
class GenericParameter(Type):

    parameter_name: str


    @property
    def name(self):

        return self.parameter_name



@dataclass(frozen=True)
class GenericInstanceType(Type):

    base_type: Type

    arguments: tuple[Type, ...]


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
class NullableType(Type):
    """A type that permits a null value."""

    base_type: Type


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

class NullType(Type):

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

    "int": INT,
    "float": FLOAT,
    "double": DOUBLE,
    "bool": BOOL,
    "char": CHAR,
    "void": VOID,

    "String": STRING,
    "Object": OBJECT
}



def resolve_builtin_type(
    name: str
):

    return BUILTIN_TYPES.get(name)