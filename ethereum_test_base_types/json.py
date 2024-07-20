"""
JSON encoding and decoding for Ethereum types.
"""

from typing import Any, AnyStr, List

from pydantic import BaseModel, RootModel


def to_json(
    input: BaseModel | RootModel | AnyStr | List[BaseModel | RootModel | AnyStr],
) -> Any:
    """
    Converts a model to its json data representation.
    """
    if isinstance(input, list):
        return [to_json(item) for item in input]
    elif isinstance(input, (BaseModel, RootModel)):
        return input.model_dump(mode="json", by_alias=True, exclude_none=True)
    else:
        return str(input)
