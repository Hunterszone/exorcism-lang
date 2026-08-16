from exorcism_types import (
    Type,
    PrimitiveType,
    ClassType,
    NullableType,
    ArrayType,
    NullType,
    FunctionType,

    INT,
    FLOAT,
    DOUBLE,
    NULL
)



class TypeSystem:


    # ========================================================
    # Assignment compatibility
    # ========================================================

    def is_assignable(
        self,
        source: Type,
        target: Type
    ) -> bool:

        # ====================================================
        # Same type
        # ====================================================

        if source == target:
            return True


        # ====================================================
        # null assignment
        #
        # null can only be assigned to nullable types.
        # ====================================================

        if isinstance(source, NullType):

            return target.nullable


        # ====================================================
        # Nullable target
        #
        # T can be assigned to T?
        # ====================================================

        if isinstance(target, NullableType):

            return self.is_assignable(
                source,
                target.base_type
            )


        # ====================================================
        # Nullable source
        #
        # T? cannot be assigned to T.
        # ====================================================

        if isinstance(source, NullableType):

            return False


        # ====================================================
        # Numeric widening
        # ====================================================

        if self.can_convert_numeric(
            source,
            target
        ):

            return True


        # ====================================================
        # Future type-system features
        # ====================================================
        #
        # inheritance
        # interfaces
        # generics
        #

        return False


    # ========================================================
    # Numeric conversions
    # ========================================================

    def can_convert_numeric(
        self,
        source: Type,
        target: Type
    ):


        if not (
            isinstance(source, PrimitiveType)
            and isinstance(target, PrimitiveType)
        ):
            return False



        conversions = {


            "char": [

                "int",
                "float",
                "double"
            ],


            "int": [

                "float",
                "double"
            ],


            "float": [

                "double"
            ]

        }


        return (

            target.name

            in conversions.get(
                source.name,
                []
            )

        )



    # ========================================================
    # Equality comparison
    # ========================================================

    def comparable(
        self,
        left: Type,
        right: Type
    ):


        if left == right:
            return True


        if (
            left.is_numeric
            and right.is_numeric
        ):
            return True


        return False



    # ========================================================
    # Binary expression result type
    # ========================================================

    def common_type(
        self,
        left: Type,
        right: Type
    ) -> Type:


        if left == right:
            return left



        numeric_order = [

            INT,
            FLOAT,
            DOUBLE

        ]


        if (
            left in numeric_order
            and right in numeric_order
        ):

            return max(
                left,
                right,
                key=numeric_order.index
            )



        raise TypeError(
            f"No common type between "
            f"{left} and {right}"
        )



    # ========================================================
    # Helpers
    # ========================================================

    def unwrap_nullable(
        self,
        t: Type
    ):

        if isinstance(
            t,
            NullableType
        ):
            return t.base_type


        return t



    def is_nullable(
        self,
        t: Type
    ):

        return t.nullable