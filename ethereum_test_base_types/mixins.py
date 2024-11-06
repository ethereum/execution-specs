"""
This module provides various mixins for Pydantic models.
"""

from typing import Any, Literal

from pydantic import BaseModel


class ModelCustomizationsMixin:
    """
    A mixin that customizes the behavior of pydantic models. Any pydantic
    configuration override that must apply to all models
    should be placed here.

    This mixin is applied to both `EthereumTestBaseModel` and `EthereumTestRootModel`.
    """

    def serialize(
        self,
        mode: Literal["json", "python"],
        by_alias: bool,
        exclude_none: bool = True,
    ) -> dict[str, Any]:
        """
        Serializes the model to the specified format with the given parameters.

        :param mode: The mode of serialization.
              If mode is 'json', the output will only contain JSON serializable types.
              If mode is 'python', the output may contain non-JSON-serializable Python objects.
        :param by_alias: Whether to use aliases for field names.
        :param exclude_none: Whether to exclude fields with None values, default is True.
        :return: The serialized representation of the model.
        """
        if not hasattr(self, "model_dump"):
            raise NotImplementedError(
                f"{self.__class__.__name__} does not have 'model_dump' method."
                "Are you sure you are using a Pydantic model?"
            )
        return self.model_dump(mode=mode, by_alias=by_alias, exclude_none=exclude_none)

    def __repr_args__(self):
        """
        Generate a list of attribute-value pairs for the object representation.

        This method serializes the model, retrieves the attribute names,
        and constructs a list of tuples containing attribute names and their corresponding values.
        Only attributes with non-None values are included in the list.

        This method is used by the __repr__ method to generate the object representation,
        and is used by `gentest` module to generate the test cases.

        See:
        - https://pydantic-docs.helpmanual.io/usage/models/#custom-repr
        - https://github.com/ethereum/execution-spec-tests/pull/901#issuecomment-2443296835

        Returns:
            List[Tuple[str, Any]]: A list of tuples where each tuple contains an attribute name
                                   and its corresponding non-None value.
        """
        attrs_names = self.serialize(mode="python", by_alias=False).keys()
        attrs = ((s, getattr(self, s)) for s in attrs_names)

        # Convert field values based on their type.
        # This ensures consistency between JSON and Python object representations.
        # Should a custom `__repr__` be needed for a specific type, it can added in the
        # match statement below.
        # Otherwise, the default string representation is used.
        repr_attrs = []
        for a, v in attrs:
            match v:

                # Note: The `None` case handles an edge case with transactions
                # see: https://github.com/ethereum/execution-spec-tests/pull/901#discussion_r1828491918 # noqa: E501
                case list() | dict() | BaseModel() | None:
                    repr_attrs.append((a, v))
                case _:
                    repr_attrs.append((a, str(v)))
        return repr_attrs
