"""Common field types from ethereum/tests."""

import re
import subprocess
import tempfile
from functools import cached_property
from typing import Any

from eth_abi import encode
from eth_utils import function_signature_to_4byte_selector
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

from ethereum_test_base_types import Address, Hash, HexNumber

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


class CodeInFillerSource:
    """Not compiled code source in test filler."""

    code_label: str | None
    code_raw: Any

    def __init__(self, code: Any, label: str | None = None):
        """Instantiate."""
        self.code_label = label
        self.code_raw = code

    @cached_property
    def compiled(self) -> bytes:
        """Compile the code from source to bytes."""
        if isinstance(self.code_raw, int):
            # Users pass code as int (very bad)
            hex_str = format(self.code_raw, "02x")
            return bytes.fromhex(hex_str)

        if not isinstance(self.code_raw, str):
            raise ValueError(f"parse_code(code: str) code is not string: {self.code_raw}")
        if len(self.code_raw) == 0:
            return b""

        compiled_code = ""

        raw_marker = ":raw 0x"
        raw_index = self.code_raw.find(raw_marker)
        abi_marker = ":abi"
        abi_index = self.code_raw.find(abi_marker)
        yul_marker = ":yul"
        yul_index = self.code_raw.find(yul_marker)

        # Parse :raw
        if raw_index != -1:
            compiled_code = self.code_raw[raw_index + len(raw_marker) :]

        # Parse :yul
        elif yul_index != -1:
            option_start = yul_index + len(yul_marker)
            options: list[str] = []
            native_yul_options: str = ""

            if self.code_raw[option_start:].lstrip().startswith("{"):
                # No yul options, proceed to code parsing
                source_start = option_start
            else:
                opt, source_start = parse_args_from_string_into_array(
                    self.code_raw, option_start + 1
                )
                for arg in opt:
                    if arg == "object" or arg == '"C"':
                        native_yul_options += arg + " "
                    else:
                        options.append(arg)

            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
                tmp.write(native_yul_options + self.code_raw[source_start:])
                tmp_path = tmp.name
            compiled_code = compile_yul(
                source_file=tmp_path,
                evm_version=options[0] if len(options) >= 1 else None,
                optimize=options[1] if len(options) >= 2 else None,
            )[2:]

        # Parse :abi
        elif abi_index != -1:
            abi_encoding = self.code_raw[abi_index + len(abi_marker) + 1 :]
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
                return function_signature + function_parameters
            return function_signature

        # Parse plain code 0x
        elif self.code_raw.lstrip().startswith("0x"):
            compiled_code = self.code_raw[2:].lower()

        # Parse lllc code
        elif self.code_raw.lstrip().startswith("{") or self.code_raw.lstrip().startswith("(asm"):
            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
                tmp.write(self.code_raw)
                tmp_path = tmp.name

            # - using lllc
            result = subprocess.run(["lllc", tmp_path], capture_output=True, text=True)

            # - using docker:
            #   If the running machine does not have lllc installed, we can use docker to run lllc,
            #   but we need to start a container first, and the process is generally slower.
            # from .docker import get_lllc_container_id
            # result = subprocess.run(
            #     ["docker", "exec", get_lllc_container_id(), "lllc", tmp_path[5:]],
            #     capture_output=True,
            #     text=True,
            # )
            compiled_code = "".join(result.stdout.splitlines())
        else:
            raise Exception(f'Error parsing code: "{self.code_raw}"')

        try:
            return bytes.fromhex(compiled_code)
        except ValueError as e:
            raise Exception(f'Error parsing compile code: "{self.code_raw}"') from e


def parse_code_label(code) -> CodeInFillerSource:
    """Parse label from code."""
    label_marker = ":label"
    label_index = code.find(label_marker)

    # Parse :label into code options
    label = None
    if label_index != -1:
        space_index = code.find(" ", label_index + len(label_marker) + 1)
        if space_index == -1:
            label = code[label_index + len(label_marker) + 1 :]
        else:
            label = code[label_index + len(label_marker) + 1 : space_index]
    return CodeInFillerSource(code, label)


AddressInFiller = Annotated[Address, BeforeValidator(lambda a: Address(a, left_padding=True))]
ValueInFiller = Annotated[HexNumber, BeforeValidator(parse_hex_number)]
CodeInFiller = Annotated[CodeInFillerSource, BeforeValidator(parse_code_label)]
Hash32InFiller = Annotated[Hash, BeforeValidator(lambda h: Hash(h, left_padding=True))]
