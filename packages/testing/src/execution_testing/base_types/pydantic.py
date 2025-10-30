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

        The implementation uses exclude_unset=True as a safe baseline, then
        explicitly adds back fields that were set via default_factory but not
        explicitly set by the user. This avoids conflicts with models that have
        mutually exclusive fields (e.g., Transaction with secret_key vs signature).
        """
        # Start with explicitly set fields (safe baseline)
        dump_dict = self.model_dump(exclude_unset=True)

        # For fields with default_factory, include them if they're not in model_fields_set
        # This handles cases like Environment.gas_limit where the factory captures
        # dynamic configuration that should be preserved in copies
        for field_name, field_info in self.__class__.model_fields.items():
            if (
                field_name not in self.model_fields_set
                and field_info.default_factory
            ):
                dump_dict[field_name] = getattr(self, field_name)

        # Merge with the updates
        dump_dict.update(kwargs)
        # Create the new instance
        new_instance = self.__class__(**dump_dict)
        # Preserve the original model_fields_set, adding any new kwargs
        new_instance.__pydantic_fields_set__ = (
            self.model_fields_set | kwargs.keys()
        )
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
