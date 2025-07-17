"""Classes to manage tags in static state tests."""

import re
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, Generic, Mapping, TypeVar

from pydantic import BaseModel, model_validator

from ethereum_test_base_types import Address, Bytes, Hash, HexNumber
from ethereum_test_types import EOA, compute_create2_address, compute_create_address

TagDict = Dict[str, Address | EOA]

T = TypeVar("T", bound=Address | Hash)


class Tag(BaseModel, Generic[T]):
    """Tag."""

    name: str
    type: ClassVar[str] = ""
    regex_pattern: ClassVar[re.Pattern] = re.compile(r"<\w+:(\w+)(:[^>]+)?")
    original_string: str | None = None  # Store the original tag string for replacement

    def __hash__(self) -> int:
        """Hash based on original string for use as dict key."""
        return hash(f"{self.__class__.__name__}:{self.name}")

    @model_validator(mode="before")
    @classmethod
    def validate_from_string(cls, data: Any) -> Any:
        """Validate the generic tag from string: <tag_kind:name:0x...>."""
        if isinstance(data, str):
            if m := cls.regex_pattern.match(data):
                name = m.group(1)
                return {"name": name, "original_string": data}
        return data

    def resolve(self, tags: TagDict) -> T:
        """Resolve the tag."""
        raise NotImplementedError("Subclasses must implement this method")


class TagDependentData(ABC):
    """Data for resolving tags."""

    @abstractmethod
    def tag_dependencies(self) -> Mapping[str, Tag]:
        """Get tag dependencies."""
        pass


class AddressTag(Tag[Address]):
    """Address tag."""

    def resolve(self, tags: TagDict) -> Address:
        """Resolve the tag."""
        assert self.name in tags, f"Tag {self.name} not found in tags"
        return Address(tags[self.name])


class ContractTag(AddressTag):
    """Contract tag."""

    type: ClassVar[str] = "contract"
    regex_pattern: ClassVar[re.Pattern] = re.compile(r"<contract:([^:>]+)(?::(0x[a-fA-F0-9]+))?>")
    debug_address: Address | None = None  # Optional hard-coded address for debugging

    @model_validator(mode="before")
    @classmethod
    def validate_from_string(cls, data: Any) -> Any:
        """Validate the contract tag from string: <contract:name:0x...> or <contract:0x...>."""
        if isinstance(data, str):
            if m := cls.regex_pattern.match(data):
                name_or_addr = m.group(1)
                debug_addr = m.group(2) if m.lastindex and m.lastindex >= 2 else None

                # Check if it's a 2-part format with an address
                if name_or_addr.startswith("0x") and len(name_or_addr) == 42:
                    # For 2-part format, use the full address as the name
                    # This ensures all references to the same address get the same tag name
                    return {
                        "name": name_or_addr,
                        "debug_address": Address(name_or_addr),
                        "original_string": data,
                    }
                else:
                    # Normal 3-part format - use the name as-is
                    result = {"name": name_or_addr, "original_string": data}
                    if debug_addr:
                        result["debug_address"] = Address(debug_addr)
                    return result
        return data


class CreateTag(AddressTag):
    """Contract derived from a another contract via CREATE."""

    create_type: str
    nonce: HexNumber | None = None
    salt: HexNumber | None = None
    initcode: Bytes | None = None

    type: ClassVar[str] = "contract"
    regex_pattern: ClassVar[re.Pattern] = re.compile(r"<(create|create2):(\w+):(\w+):?(\w+)?>")

    @model_validator(mode="before")
    @classmethod
    def validate_from_string(cls, data: Any) -> Any:
        """Validate the create tag from string: <create:name:nonce>."""
        if isinstance(data, str):
            if m := cls.regex_pattern.match(data):
                create_type = m.group(1)
                name = m.group(2)
                kwargs = {
                    "create_type": create_type,
                    "name": name,
                    "original_string": data,
                }
                if create_type == "create":
                    kwargs["nonce"] = m.group(3)
                elif create_type == "create2":
                    kwargs["salt"] = m.group(3)
                    kwargs["initcode"] = m.group(4)
                return kwargs
        return data

    def resolve(self, tags: TagDict) -> Address:
        """Resolve the tag."""
        assert self.name in tags, f"Tag {self.name} not found in tags"
        if self.create_type == "create":
            assert self.nonce is not None, "Nonce is required for create"
            return compute_create_address(address=tags[self.name], nonce=self.nonce)
        elif self.create_type == "create2":
            assert self.salt is not None, "Salt is required for create2"
            assert self.initcode is not None, "Init code is required for create2"
            return compute_create2_address(
                address=tags[self.name], salt=self.salt, initcode=self.initcode
            )
        else:
            raise ValueError(f"Invalid create type: {self.create_type}")


class SenderTag(AddressTag):
    """Sender tag."""

    type: ClassVar[str] = "eoa"
    regex_pattern: ClassVar[re.Pattern] = re.compile(r"<eoa:(\w+)(?::(0x[a-fA-F0-9]+))?>")
    debug_address: Address | None = None  # Optional hard-coded address for debugging

    @model_validator(mode="before")
    @classmethod
    def validate_from_string(cls, data: Any) -> Any:
        """Validate the sender tag from string: <eoa:name:0x...>."""
        if isinstance(data, str):
            if m := cls.regex_pattern.match(data):
                name = m.group(1)
                debug_addr = m.group(2) if m.lastindex and m.lastindex >= 2 else None

                result = {"name": name, "original_string": data}
                if debug_addr:
                    result["debug_address"] = Address(debug_addr)
                return result
        return data


class SenderKeyTag(Tag[EOA]):
    """Sender eoa tag."""

    type: ClassVar[str] = "eoa"
    regex_pattern: ClassVar[re.Pattern] = re.compile(r"<eoa:(\w+)(?::(0x[a-fA-F0-9]+))?>")
    debug_key: str | None = None  # Optional hard-coded key for debugging

    @model_validator(mode="before")
    @classmethod
    def validate_from_string(cls, data: Any) -> Any:
        """Validate the sender key tag from string: <eoa:name:0xkey...>."""
        if isinstance(data, str):
            if m := cls.regex_pattern.match(data):
                name = m.group(1)
                debug_key = m.group(2) if m.lastindex and m.lastindex >= 2 else None

                result = {"name": name, "original_string": data}
                if debug_key:
                    result["debug_key"] = debug_key
                return result
        return data

    def resolve(self, tags: TagDict) -> EOA:
        """Resolve the tag."""
        assert self.name in tags, f"Tag {self.name} not found in tags"
        result = tags[self.name]
        assert isinstance(result, EOA), f"Expected EOA but got {type(result)} for tag {self.name}"
        return result
