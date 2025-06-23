from typing import (
    Any,
    Dict,
    Type,
)

from pydantic import (
    BaseModel,
    ConfigDict,
)
from pydantic._internal._core_utils import (
    CoreSchemaField,
)
from pydantic.alias_generators import (
    to_camel,
)
from pydantic.json_schema import (
    DEFAULT_REF_TEMPLATE,
    GenerateJsonSchema,
    JsonSchemaMode,
)


class OmitJsonSchema(GenerateJsonSchema):
    """
    Custom JSON schema generator that omits the schema generation for fields that are
    invalid. Excluded fields (``Field(exclude=True)``) are generally useful as
    properties of the model but are not meant to be serialized to JSON.
    """

    def field_is_present(self, field: CoreSchemaField) -> bool:
        # override ``field_is_present`` and omit excluded fields from the schema
        if field.get("serialization_exclude", False):
            return False
        return super().field_is_present(field)


class CamelModel(BaseModel):
    """
    Camel-case pydantic model. This model is used to ensure serialization in a
    consistent manner, aliasing as camelCase serialization. This is useful for models
    that are used in JSON-RPC requests and responses, marking useful fields for the
    model, but that are not part of the JSON-RPC object, with ``Field(exclude=True)``.
    To serialize a model to the expected JSON-RPC format, or camelCase, use
    ``model_dump(by_alias=True)``.

    .. code-block:: python

        >>> from eth_utils.pydantic import CamelModel
        >>> from pydantic import Field

        >>> class SignedSetCodeAuthorization(CamelModel):
        ...     chain_id: int
        ...     address: bytes
        ...     nonce: int
        ...
        ...     # useful fields for the object but excluded from serialization
        ...     # (not part of the JSON-RPC object)
        ...     authorization_hash: bytes = Field(exclude=True)
        ...     signature: bytes = Field(exclude=True)

        >>> auth = SignedSetCodeAuthorization(
        ...     chain_id=1,
        ...     address=b"0x0000000000000000000000000000000000000000",
        ...     nonce=0,
        ...     authorization_hash=generated_hash,
        ...     signature=generated_signature,
        ... )
        >>> auth.model_dump(by_alias=True)
        {'chainId': 1, 'address': '0x000000000000000000000000000000000000', 'nonce': 0}
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        # populate by snake_case (python) args
        populate_by_name=True,
        # serialize by camelCase (json-rpc) keys
        alias_generator=to_camel,
        # validate default values
        validate_default=True,
    )

    @classmethod
    def model_json_schema(
        cls,
        by_alias: bool = True,
        ref_template: str = DEFAULT_REF_TEMPLATE,
        # default to ``OmitJsonSchema`` to prevent errors from excluded fields
        schema_generator: Type[GenerateJsonSchema] = OmitJsonSchema,
        mode: JsonSchemaMode = "validation",
    ) -> Dict[str, Any]:
        """
        Omits excluded fields from the JSON schema, preventing errors that would
        otherwise be raised by the default schema generator.
        """
        return super().model_json_schema(
            by_alias=by_alias,
            ref_template=ref_template,
            schema_generator=schema_generator,
            mode=mode,
        )
