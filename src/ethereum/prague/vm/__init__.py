"""
Ethereum Virtual Machine (EVM)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

The abstract computer which runs the code stored in an
`.fork_types.Account`.
"""

import enum
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple, Union

from ethereum.base_types import U64, U256, Bytes, Bytes0, Bytes32, Uint
from ethereum.crypto.hash import Hash32

from ..blocks import Log
from ..fork_types import Address, Authorization, VersionedHash
from ..state import State, TransientStorage, account_exists_and_is_empty
from .exceptions import InvalidEof
from .precompiled_contracts import RIPEMD160_ADDRESS

__all__ = ("Environment", "Evm", "Message", "Eof")


EOF_MAGIC = b"\xEF\x00"
EOF_MAGIC_LENGTH = len(EOF_MAGIC)

MAX_CODE_SIZE = 0x6000


class Eof(enum.Enum):
    """
    Enumeration of the different kinds of EOF containers.
    Legacy code is assigned zero.
    """

    LEGACY = 0
    EOF1 = 1


@dataclass
class EofMetadata:
    """
    Dataclass to hold the metadata information of the
    EOF container.
    """

    type_size: Uint
    num_code_sections: Uint
    code_sizes: List[Uint]
    num_container_sections: Uint
    container_sizes: List[Uint]
    data_size: Uint
    body_start_index: Uint
    type_section_contents: List[bytes]
    code_section_contents: List[bytes]
    container_section_contents: List[bytes]
    data_section_contents: bytes


@dataclass
class ReturnStackItem:
    """
    Stack item for the return stack.
    """

    code_section_index: Uint
    offset: Uint


@dataclass
class OpcodeStackItemCount:
    """
    Stack height count for an Opcode.
    """

    inputs: int
    outputs: int


@dataclass
class Environment:
    """
    Items external to the virtual machine itself, provided by the environment.
    """

    caller: Address
    block_hashes: List[Hash32]
    origin: Address
    coinbase: Address
    number: Uint
    base_fee_per_gas: Uint
    gas_limit: Uint
    gas_price: Uint
    time: U256
    prev_randao: Bytes32
    state: State
    chain_id: U64
    traces: List[dict]
    excess_blob_gas: U64
    blob_versioned_hashes: Tuple[VersionedHash, ...]
    transient_storage: TransientStorage


@dataclass
class Message:
    """
    Items that are used by contract creation or message call.
    """

    caller: Address
    target: Union[Bytes0, Address]
    current_target: Address
    gas: Uint
    value: U256
    data: Bytes
    code_address: Optional[Address]
    code: Bytes
    depth: Uint
    should_transfer_value: bool
    is_static: bool
    accessed_addresses: Set[Address]
    accessed_storage_keys: Set[Tuple[Address, Bytes32]]
    parent_evm: Optional["Evm"]
    authorizations: Tuple[Authorization, ...]
    is_init_container: Optional[bool]


@dataclass
class Evm:
    """The internal state of the virtual machine."""

    pc: Uint
    stack: List[U256]
    memory: bytearray
    code: Bytes
    gas_left: Uint
    env: Environment
    valid_jump_destinations: Set[Uint]
    logs: Tuple[Log, ...]
    refund_counter: int
    running: bool
    message: Message
    output: Bytes
    accounts_to_delete: Set[Address]
    touched_accounts: Set[Address]
    return_data: Bytes
    error: Optional[Exception]
    accessed_addresses: Set[Address]
    accessed_storage_keys: Set[Tuple[Address, Bytes32]]
    eof_version: Eof
    eof_container: Optional[Bytes]
    eof_metadata: Optional[EofMetadata]
    current_section_index: Uint
    return_stack: List[ReturnStackItem]
    deploy_container: Optional[Bytes]


def incorporate_child_on_success(evm: Evm, child_evm: Evm) -> None:
    """
    Incorporate the state of a successful `child_evm` into the parent `evm`.

    Parameters
    ----------
    evm :
        The parent `EVM`.
    child_evm :
        The child evm to incorporate.
    """
    evm.gas_left += child_evm.gas_left
    evm.logs += child_evm.logs
    evm.refund_counter += child_evm.refund_counter
    evm.accounts_to_delete.update(child_evm.accounts_to_delete)
    evm.touched_accounts.update(child_evm.touched_accounts)
    if account_exists_and_is_empty(
        evm.env.state, child_evm.message.current_target
    ):
        evm.touched_accounts.add(child_evm.message.current_target)
    evm.accessed_addresses.update(child_evm.accessed_addresses)
    evm.accessed_storage_keys.update(child_evm.accessed_storage_keys)


def incorporate_child_on_error(evm: Evm, child_evm: Evm) -> None:
    """
    Incorporate the state of an unsuccessful `child_evm` into the parent `evm`.

    Parameters
    ----------
    evm :
        The parent `EVM`.
    child_evm :
        The child evm to incorporate.
    """
    # In block 2675119, the empty account at 0x3 (the RIPEMD160 precompile) was
    # cleared despite running out of gas. This is an obscure edge case that can
    # only happen to a precompile.
    # According to the general rules governing clearing of empty accounts, the
    # touch should have been reverted. Due to client bugs, this event went
    # unnoticed and 0x3 has been exempted from the rule that touches are
    # reverted in order to preserve this historical behaviour.
    if RIPEMD160_ADDRESS in child_evm.touched_accounts:
        evm.touched_accounts.add(RIPEMD160_ADDRESS)
    if child_evm.message.current_target == RIPEMD160_ADDRESS:
        if account_exists_and_is_empty(
            evm.env.state, child_evm.message.current_target
        ):
            evm.touched_accounts.add(RIPEMD160_ADDRESS)
    evm.gas_left += child_evm.gas_left


def get_eof_version(code: bytes) -> Eof:
    """
    Get the Eof container's version.

    Parameters
    ----------
    code : bytes
        The code to check.

    Returns
    -------
    Eof
        Eof Version of the container.
    """
    if not code.startswith(EOF_MAGIC):
        return Eof.LEGACY

    if code[EOF_MAGIC_LENGTH] == 1:
        return Eof.EOF1
    else:
        raise InvalidEof("Invalid EOF version")
