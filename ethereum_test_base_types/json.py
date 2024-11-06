"""
JSON encoding and decoding for Ethereum types.
"""

from typing import Any, AnyStr, List

from .pydantic import EthereumTestBaseModel, EthereumTestRootModel


def to_json(
    input: (
        EthereumTestBaseModel
        | EthereumTestRootModel
        | AnyStr
        | List[EthereumTestBaseModel | EthereumTestRootModel | AnyStr]
    ),
) -> Any:
    """
    Converts a model to its json data representation.
    """
    if isinstance(input, list):
        return [to_json(item) for item in input]
    elif isinstance(input, (EthereumTestBaseModel, EthereumTestRootModel)):
        return input.serialize(mode="json", by_alias=True)
    else:
        return str(input)
