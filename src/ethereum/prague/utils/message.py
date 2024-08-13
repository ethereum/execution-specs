"""
Hardfork Utility Functions For The Message Data-structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Message specific functions used in this prague version of
specification.
"""
from typing import FrozenSet, Optional, Tuple, Union

from ethereum.base_types import U256, Bytes, Bytes0, Bytes32, Uint

from ..fork_types import Address, Authorization
from ..state import get_account
from ..vm import Environment, Eof, EofVersion, Message, get_eof_version
from ..vm.eof.utils import metadata_from_container
from ..vm.eof.validation import parse_create_tx_call_data
from ..vm.precompiled_contracts.mapping import PRE_COMPILED_CONTRACTS
from .address import compute_contract_address_1


def prepare_message(
    caller: Address,
    target: Union[Bytes0, Address],
    value: U256,
    data: Bytes,
    gas: Uint,
    env: Environment,
    code_address: Optional[Address] = None,
    should_transfer_value: bool = True,
    is_static: bool = False,
    preaccessed_addresses: FrozenSet[Address] = frozenset(),
    preaccessed_storage_keys: FrozenSet[
        Tuple[(Address, Bytes32)]
    ] = frozenset(),
    authorizations: Tuple[Authorization, ...] = (),
) -> Message:
    """
    Execute a transaction against the provided environment.

    Parameters
    ----------
    caller :
        Address which initiated the transaction
    target :
        Address whose code will be executed
    value :
        Value to be transferred.
    data :
        Array of bytes provided to the code in `target`.
    gas :
        Gas provided for the code in `target`.
    env :
        Environment for the Ethereum Virtual Machine.
    code_address :
        This is usually same as the `target` address except when an alternative
        accounts code needs to be executed.
        eg. `CALLCODE` calling a precompile.
    should_transfer_value :
        if True ETH should be transferred while executing a message call.
    is_static:
        if True then it prevents all state-changing operations from being
        executed.
    preaccessed_addresses:
        Addresses that should be marked as accessed prior to the message call
    preaccessed_storage_keys:
        Storage keys that should be marked as accessed prior to the message
        call
    authorizations:
        Authorizations that should be applied to the message call.

    Returns
    -------
    message: `ethereum.prague.vm.Message`
        Items containing contract creation or message call specific data.
    """
    if isinstance(target, Bytes0):
        current_target = compute_contract_address_1(
            caller,
            get_account(env.state, caller).nonce - U256(1),
        )
        if get_eof_version(data) == EofVersion.LEGACY:
            msg_data = Bytes(b"")
            code = data
            eof = None
        else:
            eof, msg_data = parse_create_tx_call_data(data)
            code = eof.container
    elif isinstance(target, Address):
        current_target = target
        msg_data = data
        code = get_account(env.state, target).code
        if code_address is None:
            code_address = target

        if get_eof_version(code) == EofVersion.LEGACY:
            eof = None
        else:
            metadata = metadata_from_container(
                code,
                validate=False,
                is_deploy_container=False,
                is_init_container=False,
            )
            eof = Eof(
                version=get_eof_version(code),
                container=code,
                metadata=metadata,
                is_init_container=False,
                is_deploy_container=False,
            )
    else:
        raise AssertionError("Target must be address or empty bytes")

    accessed_addresses = set()
    accessed_addresses.add(current_target)
    accessed_addresses.add(caller)
    accessed_addresses.update(PRE_COMPILED_CONTRACTS.keys())
    accessed_addresses.update(preaccessed_addresses)

    return Message(
        caller=caller,
        target=target,
        gas=gas,
        value=value,
        data=msg_data,
        code=code,
        depth=Uint(0),
        current_target=current_target,
        code_address=code_address,
        should_transfer_value=should_transfer_value,
        is_static=is_static,
        accessed_addresses=accessed_addresses,
        accessed_storage_keys=set(preaccessed_storage_keys),
        parent_evm=None,
        authorizations=authorizations,
        eof=eof,
    )
