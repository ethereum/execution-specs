"""Base pydantic classes used to define the models for Ethereum tests."""

from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict, RootModel
from pydantic.alias_generators import to_camel
from typing_extensions import Self

from .mixins import ModelCustomizationsMixin

RootModelRootType = TypeVar("RootModelRootType")


class EthereumTestBaseModel(BaseModel, ModelCustomizationsMixin):
    """Base model for all models for Ethereum tests."""

    pass


class EthereumTestRootModel(
    RootModel[RootModelRootType], ModelCustomizationsMixin
):
    """Base model for all models for Ethereum tests."""

    root: Any


class CopyValidateModel(EthereumTestBaseModel):
    """Model that supports copying with validation."""

    def copy(self: Self, **kwargs: Any) -> Self:
        """
        Create a copy of the model with the updated fields that are validated.

        This method preserves the actual field values (including those set via
        default_factory) while maintaining the model_fields_set to track which
        fields were explicitly set.
        """
        # Get all current field values, including those set via default_factory
        dump_dict = self.model_dump()
        # Merge with the updates
        dump_dict.update(kwargs)
        # Create the new instance
        new_instance = self.__class__(**dump_dict)
        # Preserve the original model_fields_set, adding any new kwargs
        new_instance.__pydantic_fields_set__ = self.model_fields_set | kwargs.keys()
        return new_instance


class CamelModel(CopyValidateModel):
    """
    A base model that converts field names to camel case when serializing.

    For example, the field name `current_timestamp` in a Python model will be
    represented as `currentTimestamp` when it is serialized to json.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        validate_default=True,
    )
