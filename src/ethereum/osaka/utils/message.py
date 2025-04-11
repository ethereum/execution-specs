"""
Hardfork Utility Functions For The Message Data-structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Message specific functions used in this osaka version of
specification.
"""
from ethereum_types.bytes import Bytes, Bytes0
from ethereum_types.numeric import Uint

from ..fork_types import Address
from ..state import get_account
from ..transactions import Transaction
from ..vm import BlockEnvironment, Message, TransactionEnvironment
from ..vm.eoa_delegation import get_delegated_code_address
from ..vm.eof import ContainerContext, Eof, EofVersion, get_eof_version
from ..vm.eof.utils import metadata_from_container
from ..vm.eof.validation import parse_create_tx_call_data
from ..vm.precompiled_contracts.mapping import PRE_COMPILED_CONTRACTS
from .address import compute_contract_address


def prepare_message(
    block_env: BlockEnvironment,
    tx_env: TransactionEnvironment,
    tx: Transaction,
) -> Message:
    """
    Execute a transaction against the provided environment.

    Parameters
    ----------
    block_env :
        Environment for the Ethereum Virtual Machine.
    tx_env :
        Environment for the transaction.
    tx :
        Transaction to be executed.

    Returns
    -------
    message: `ethereum.osaka.vm.Message`
        Items containing contract creation or message call specific data.
    """
    accessed_addresses = set()
    accessed_addresses.add(tx_env.origin)
    accessed_addresses.update(PRE_COMPILED_CONTRACTS.keys())
    accessed_addresses.update(tx_env.access_list_addresses)

    is_delegated = False

    if isinstance(tx.to, Bytes0):
        current_target = compute_contract_address(
            tx_env.origin,
            get_account(block_env.state, tx_env.origin).nonce - Uint(1),
        )
        if get_eof_version(tx.data) == EofVersion.LEGACY:
            msg_data = Bytes(b"")
            code = tx.data
            eof = None
        else:
            eof, msg_data = parse_create_tx_call_data(tx.data)
            code = eof.container
        code_address = None
    elif isinstance(tx.to, Address):
        current_target = tx.to
        msg_data = tx.data
        code = get_account(block_env.state, tx.to).code

        delegated_address = get_delegated_code_address(code)
        if delegated_address is not None:
            is_delegated = True
            accessed_addresses.add(delegated_address)
            code = get_account(block_env.state, delegated_address).code

        code_address = tx.to

        if get_eof_version(code) == EofVersion.LEGACY:
            eof = None
        else:
            metadata = metadata_from_container(
                code,
                validate=False,
                context=ContainerContext.RUNTIME,
            )
            eof = Eof(
                version=get_eof_version(code),
                container=code,
                metadata=metadata,
            )
    else:
        raise AssertionError("Target must be address or empty bytes")

    accessed_addresses.add(current_target)

    return Message(
        block_env=block_env,
        tx_env=tx_env,
        caller=tx_env.origin,
        target=tx.to,
        gas=tx_env.gas,
        value=tx.value,
        data=msg_data,
        code=code,
        depth=Uint(0),
        current_target=current_target,
        code_address=code_address,
        should_transfer_value=True,
        is_static=False,
        accessed_addresses=accessed_addresses,
        accessed_storage_keys=set(tx_env.access_list_storage_keys),
        is_delegated=is_delegated,
        parent_evm=None,
        eof=eof,
    )
