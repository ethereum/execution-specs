"""
The module implements the raw EVM tracer for pytest
"""
import logging
from dataclasses import dataclass
from typing import Any, List

from ethereum.base_types import U256, Bytes, Uint


@dataclass
class EvmTrace:
    """
    The object that is logged when pytest log_cli_level
    is set to 10. This can be used to create a raw trace of the evm.

    Contains the following:

          1. `depth`: depth of the message
          2. `pc`: programcounter before opcode execution
          3. `op`: the opcode to be executed
          4. `has_erred`: has the evm erred before execution
          5. `start_gas`: evm.gas_left before execution starts
          6. `refund`: refund counter before opcode execution
          7. `output`: evm output
          8. `stack`: the stack before opcode execution
    """

    depth: Uint
    pc: Uint
    op: str
    has_erred: bool
    start_gas: U256
    refund: U256
    output: Bytes
    stack: List[U256]

    def custom_repr(self) -> str:
        """
        Add indentation for child evms (depth > 0)
        """
        tabs = "\t" * self.depth
        rep = tabs + self.__repr__()
        return rep


def evm_trace(evm: Any, op: Any) -> None:
    """
    Create a new trace instance before opcode execution
    """
    if isinstance(op, bytes):
        opcode = "0x" + op.hex().lstrip("00")
    else:
        opcode = str(op).split(".")[-1]

    new_trace = EvmTrace(
        depth=evm.message.depth,
        pc=evm.pc,
        op=opcode,
        has_erred=False,
        start_gas=evm.gas_left,
        refund=evm.refund_counter,
        output=evm.output,
        stack=evm.stack.copy(),
    )
    logging.info(new_trace.custom_repr())
