"""Common field types from ethereum/tests."""

import re
import subprocess
import tempfile
from typing import Tuple

from eth_abi import encode
from eth_utils import function_signature_to_4byte_selector
from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

from ethereum_test_base_types import Address, Bytes, Hash, HexNumber

from .compile_yul import compile_yul


def parse_hex_number(i: str | int) -> int:
    """Check if the given string is a valid hex number."""
    if i == "" or i == "0x":
        return 0
    if isinstance(i, int):
        return i
    if i.startswith("0x:bigint "):
        i = i[10:]
        return int(i, 16)
    if i.startswith("0x") or any(char in "abcdef" for char in i.lower()):
        return int(i, 16)
    return int(i, 10)


class CodeOptions(BaseModel):
    """Define options of the code."""

    label: str = Field("")


def parse_args_from_string_into_array(stream: str, pos: int, delim: str = " "):
    """Parse YUL options into array."""
    args = []
    arg = ""
    # Loop until end of stream or until encountering newline or '{'
    while pos < len(stream) and stream[pos] not in ("\n", "{"):
        if stream[pos] == delim:
            args.append(arg)
            arg = ""
        else:
            arg += stream[pos]
        pos += 1
    if arg:
        args.append(arg)
    return args, pos


def parse_code(code: str) -> Tuple[bytes, CodeOptions]:
    """Check if the given string is a valid code."""
    # print("parse `" + str(code) + "`")
    if isinstance(code, int):
        # Users pass code as int (very bad)
        hex_str = format(code, "02x")
        return (bytes.fromhex(hex_str), CodeOptions())
    if not isinstance(code, str):
        raise ValueError(f"parse_code(code: str) code is not string: {code}")
    if len(code) == 0:
        return (bytes.fromhex(""), CodeOptions())

    compiled_code = ""
    code_options: CodeOptions = CodeOptions()

    raw_marker = ":raw 0x"
    raw_index = code.find(raw_marker)
    abi_marker = ":abi"
    abi_index = code.find(abi_marker)
    label_marker = ":label"
    label_index = code.find(label_marker)
    yul_marker = ":yul"
    yul_index = code.find(yul_marker)

    # Parse :label into code options
    if label_index != -1:
        space_index = code.find(" ", label_index + len(label_marker) + 1)
        if space_index == -1:
            label = code[label_index + len(label_marker) + 1 :]
        else:
            label = code[label_index + len(label_marker) + 1 : space_index]
        code_options.label = label

    # Prase :raw
    if raw_index != -1:
        compiled_code = code[raw_index + len(raw_marker) :]

    elif yul_index != -1:
        option_start = yul_index + len(yul_marker)
        options: list[str] = []
        native_yul_options: str = ""

        if code[option_start:].lstrip().startswith("{"):
            # No yul options, proceed to code parsing
            source_start = option_start
        else:
            opt, source_start = parse_args_from_string_into_array(code, option_start + 1)
            for arg in opt:
                if arg == "object" or arg == '"C"':
                    native_yul_options += arg + " "
                else:
                    options.append(arg)

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp.write(native_yul_options + code[source_start:])
            tmp_path = tmp.name
        compiled_code = compile_yul(
            source_file=tmp_path,
            evm_version=options[0] if len(options) >= 1 else None,
            optimize=options[1] if len(options) >= 2 else None,
        )[2:]

    # Prase :abi
    elif abi_index != -1:
        abi_encoding = code[abi_index + len(abi_marker) + 1 :]
        tokens = abi_encoding.strip().split()
        abi = tokens[0]
        function_signature = function_signature_to_4byte_selector(abi)
        parameter_str = re.sub(r"^\w+", "", abi).strip()

        parameter_types = parameter_str.strip("()").split(",")
        if len(tokens) > 1:
            function_parameters = encode(
                [parameter_str],
                [
                    [
                        int(t.lower(), 0) & ((1 << 256) - 1)  # treat big ints as 256bits
                        if parameter_types[t_index] == "uint"
                        else int(t.lower(), 0) > 0  # treat positive values as True
                        if parameter_types[t_index] == "bool"
                        else False and ValueError("unhandled parameter_types")
                        for t_index, t in enumerate(tokens[1:])
                    ]
                ],
            )
            return (function_signature + function_parameters, code_options)
        return (function_signature, code_options)

    # Prase plain code 0x
    elif code.lstrip().startswith("0x"):
        compiled_code = code[2:].lower()

    # Prase lllc code
    elif code.lstrip().startswith("{") or code.lstrip().startswith("(asm"):
        binary_path = "lllc"
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp.write(code)
            tmp_path = tmp.name
        result = subprocess.run([binary_path, tmp_path], capture_output=True, text=True)
        compiled_code = "".join(result.stdout.splitlines())
    else:
        raise Exception(f'Error parsing code: "{code}"')

    try:
        return (bytes.fromhex(compiled_code), code_options)
    except ValueError as e:
        raise Exception(f'Error parsing compile code: "{code}"') from e


AddressInFiller = Annotated[Address, BeforeValidator(lambda a: Address(a, left_padding=True))]
ValueInFiller = Annotated[HexNumber, BeforeValidator(parse_hex_number)]
CodeInFiller = Annotated[Tuple[Bytes, CodeOptions], BeforeValidator(parse_code)]
Hash32InFiller = Annotated[Hash, BeforeValidator(lambda h: Hash(h, left_padding=True))]
