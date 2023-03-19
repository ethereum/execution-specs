import json
from typing import Any, Dict, List
from dataclasses import dataclass

from ethereum.base_types import U64, U256, Uint, Bytes
from ethereum.crypto.hash import keccak256
from ethereum.crypto.elliptic_curve import secp256k1_sign
from ethereum.utils.hexadecimal import hex_to_u64, hex_to_u256, hex_to_uint, hex_to_bytes, Hash32


def read_hex_or_int(value, to_type):
    # find the function based on the type
    if to_type == Uint:
        to_type_func = hex_to_uint
    elif to_type == U256:
        to_type_func = hex_to_u256
    elif to_type == U64:
        to_type_func = hex_to_u64
    else:
        raise Exception("Unknown type")

    # if the value is a hex string, convert it
    if isinstance(value, str) and value.startswith("0x"):
        return to_type_func(value)
    # if the value is an str, convert it
    else:
        return to_type(int(value))


class FatalException(Exception):
    pass


def ensure_success(fn, *args):

    try:
        return fn(*args)
    except Exception as e:
        raise FatalException(e)


def get_module_name(forks, state_fork):

    exception_maps = {
        "EIP150": "tangerine_whistle",
        "EIP158": "spurious_dragon",
    }

    if state_fork in exception_maps:
        return exception_maps[state_fork]

    for fork in forks:
        value = fork.name.split(".")[-1]
        key_items = [x.title() for x in value.split("_")]
        key = "".join(key_items)

        if key == state_fork:
            return value

