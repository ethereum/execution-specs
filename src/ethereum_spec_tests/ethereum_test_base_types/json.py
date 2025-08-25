"""JSON encoding and decoding for Ethereum types."""

from typing import Any, AnyStr, List

from .pydantic import EthereumTestBaseModel, EthereumTestRootModel


def to_json(
    input_model: (
        EthereumTestBaseModel
        | EthereumTestRootModel
        | AnyStr
        | List[EthereumTestBaseModel | EthereumTestRootModel | AnyStr]
    ),
) -> Any:
    """Convert a model to its json data representation."""
    if isinstance(input_model, list):
        return [to_json(item) for item in input_model]
    elif isinstance(input_model, (EthereumTestBaseModel, EthereumTestRootModel)):
        return input_model.model_dump(mode="json", by_alias=True, exclude_none=True)
    else:
        return str(input_model)
