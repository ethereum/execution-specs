"""Test the conversion of values recorded by evaluation tests."""

from enum import Enum, IntEnum
from typing import Any
from unittest.mock import Mock

import execnet
import pytest
from ethereum_types.numeric import U256, Uint
from pydantic import BaseModel

from execution_testing.base_types import (
    Address,
    Bytes,
    Hash,
    HexNumber,
    Number,
)
from execution_testing.client_clis import TransitionTool
from execution_testing.forks import Cancun

from ..evaluate import SpecRunner, _to_primitive


class Color(Enum):
    """A plain enum."""

    RED = "red"


class Level(IntEnum):
    """An integer enum."""

    HIGH = 2


class Finding(BaseModel):
    """A pydantic model with a field of a framework type."""

    address: Address
    gas: HexNumber


class CustomValue:
    """A value of a type the converter does not know."""


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param(None, None, id="none"),
        pytest.param(True, True, id="bool"),
        pytest.param(1, 1, id="int"),
        pytest.param(1.5, 1.5, id="float"),
        pytest.param("text", "text", id="str"),
        pytest.param(HexNumber(0x5208), 21000, id="hex_number"),
        pytest.param(Number(7), 7, id="number"),
        pytest.param(Uint(8), 8, id="uint"),
        pytest.param(U256(9), 9, id="u256"),
        pytest.param(
            Address(1),
            "0x0000000000000000000000000000000000000001",
            id="address",
        ),
        pytest.param(Hash(2), "0x" + "00" * 31 + "02", id="hash"),
        pytest.param(Bytes(b"\x01\x02"), "0x0102", id="base_bytes"),
        pytest.param(b"\x01\x02", "0x0102", id="bytes"),
        pytest.param(Color.RED, "red", id="enum"),
        pytest.param(Level.HIGH, 2, id="int_enum"),
        pytest.param(
            Finding(address=Address(1), gas=HexNumber(5)),
            {
                "address": "0x0000000000000000000000000000000000000001",
                "gas": "0x5",
            },
            id="pydantic_model",
        ),
        pytest.param((1, HexNumber(2)), [1, 2], id="tuple"),
        pytest.param({HexNumber(3)}, [3], id="set"),
        pytest.param(
            {1: {"addresses": [Address(1)]}},
            {
                "1": {
                    "addresses": ["0x0000000000000000000000000000000000000001"]
                }
            },
            id="nested_dict",
        ),
    ],
)
def test_to_primitive(value: Any, expected: Any) -> None:
    """Test that values are converted to the expected built-in values."""
    converted = _to_primitive(value)
    assert converted == expected
    assert type(converted) is type(expected)


def test_to_primitive_keeps_bool() -> None:
    """Test that a `bool` is not converted to an `int`."""
    assert _to_primitive(False) is False


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(CustomValue(), id="unknown_type"),
        pytest.param([1, CustomValue()], id="nested_unknown_type"),
    ],
)
def test_to_primitive_rejects_unknown_types(value: Any) -> None:
    """Test that a value of an unknown type raises instead of a string."""
    with pytest.raises(TypeError, match="CustomValue"):
        _to_primitive(value)


def test_to_primitive_is_serializable_by_xdist() -> None:
    """
    Test that converted records can be sent from an xdist worker.

    xdist workers send reports to the controller with execnet, which
    rejects subclasses of built-in types such as `HexNumber`.
    """
    records = {
        "gas_used": HexNumber(21000),
        "sender": Address(1),
        "values": (HexNumber(1), Bytes(b"\x01")),
    }
    with pytest.raises(execnet.DumpError):
        execnet.dumps(records)
    converted = _to_primitive(records)
    assert execnet.loads(execnet.dumps(converted)) == converted


def test_record_converts_values() -> None:
    """Test that `SpecRunner.record` stores converted values."""
    spec = SpecRunner(t8n=Mock(spec=TransitionTool), fork=Cancun)
    spec.record(gas_used=HexNumber(21000), deployed=True)
    assert spec.records == {"gas_used": 21000, "deployed": True}
    assert type(spec.records["gas_used"]) is int


def test_record_rejects_unknown_types() -> None:
    """Test that `SpecRunner.record` raises on a value of unknown type."""
    spec = SpecRunner(t8n=Mock(spec=TransitionTool), fork=Cancun)
    with pytest.raises(TypeError, match="CustomValue"):
        spec.record(value=CustomValue())
