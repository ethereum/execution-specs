"""
JSON encoding and decoding for Ethereum types.
"""
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from dataclasses import fields, is_dataclass
from typing import Any, Callable, Dict, Optional


class SupportsJSON(ABC):
    """
    Interface for objects that can be converted to JSON.
    """

    @abstractmethod
    def __json__(self, encoder: "JSONEncoder") -> Any:
        """
        Converts the object to JSON.
        """
        raise NotImplementedError()


class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for `ethereum_test` types.
    """

    @dataclass(kw_only=True)
    class Field:
        """
        Settings for a field in a JSON object.
        """

        name: Optional[str] = None
        """
        The name of the field in the JSON object.
        """
        cast_type: Optional[Callable] = None
        """
        The type or function to use to cast the field to before serializing.
        """
        skip_string_convert: bool = False
        """
        By default, the fields are converted to string after serializing.
        """
        to_json: bool = False
        """
        Whether the field should be converted to JSON by itself.
        This option and `JSON_SKIP_STRING_CONVERT` are mutually exclusive.
        """
        default_value: Optional[Any] = None
        """
        Value to use if the field is not set before type casting.
        """
        default_value_skip_cast: Optional[Any] = None
        """
        Value to use if the field is not set and also skip type casting.
        """
        keep_none: bool = False
        """
        Whether to keep the field if it is `None`.
        """
        skip: bool = False
        """
        Whether to skip the field when serializing.
        """

        def apply(
            self, encoder: json.JSONEncoder, target: Dict[str, Any], field_name: str, value: Any
        ) -> None:
            """
            Applies the settings to the target dictionary.
            """
            if self.skip:
                return

            if self.name:
                field_name = self.name

            if value is None:
                if self.default_value is not None:
                    value = self.default_value
                elif self.default_value_skip_cast is not None:
                    target[field_name] = self.default_value_skip_cast
                    return

                if not self.keep_none and value is None:
                    return

            if value is not None:
                if self.cast_type is not None:
                    value = self.cast_type(value)

                if self.to_json:
                    value = encoder.default(value)
                elif not self.skip_string_convert:
                    value = str(value)

            target[field_name] = value

    def default(self, obj: Any) -> Any:
        """
        Encodes types defined in this module using basic python facilities.
        """
        if callable(getattr(obj, "__json__", False)):
            return obj.__json__(encoder=self)

        elif is_dataclass(obj):
            result: Dict[str, Any] = {}
            for object_field in fields(obj):
                field_name = object_field.name
                metadata = object_field.metadata
                value = getattr(obj, field_name)
                assert metadata is not None, f"Field {field_name} has no metadata"
                field_settings = metadata.get("json_encoder")
                assert isinstance(field_settings, self.Field), (
                    f"Field {field_name} has invalid json_encoder " f"metadata: {field_settings}"
                )
                field_settings.apply(self, result, field_name, value)
            return result

        elif isinstance(obj, dict):
            return {self.default(k): self.default(v) for k, v in obj.items()}

        elif isinstance(obj, list) or isinstance(obj, tuple):
            return [self.default(item) for item in obj]

        elif isinstance(obj, str) or isinstance(obj, int) or isinstance(obj, bool) or obj is None:
            return obj

        else:
            return super().default(obj)


def field(*args, json_encoder: Optional[JSONEncoder.Field] = None, **kwargs) -> Any:
    """
    A wrapper around `dataclasses.field` that allows for json configuration info.
    """
    if "metadata" in kwargs:
        metadata = kwargs["metadata"]
    else:
        metadata = {}
    assert isinstance(metadata, dict)

    if json_encoder is not None:
        metadata["json_encoder"] = json_encoder

    kwargs["metadata"] = metadata
    return dataclass_field(*args, **kwargs)


def to_json(input: Any) -> Dict[str, Any]:
    """
    Converts a value to its json representation.
    """
    return JSONEncoder().default(input)
