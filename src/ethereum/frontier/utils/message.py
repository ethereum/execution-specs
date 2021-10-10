"""
Frontier Utility Functions For The Message Data-structure
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. contents:: Table of Contents
    :backlinks: none
    :local:

Introduction
------------

Message specific functions used in this frontier version of specification.
"""
from typing import Optional, Union

from ethereum.base_types import U256, Bytes, Bytes0, Uint

from ..eth_types import Address
from ..state import get_account
from ..vm import Environment, Message
from .address import compute_contract_address


def prepare_message(
    caller: Address,
    target: Union[Bytes0, Address],
    value: U256,
    data: Bytes,
    gas: U256,
    env: Environment,
    code_address: Optional[Address] = None,
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

    Returns
    -------
    message: `ethereum.frontier.vm.Message`
        Items containing contract creation or message call specific data.
    """
    if isinstance(target, Bytes0):
        current_target = compute_contract_address(
            caller,
            get_account(env.state, caller).nonce - U256(1),
        )
        msg_data = Bytes(b"")
        code = data
    elif isinstance(target, Address):
        current_target = target
        msg_data = data
        code = get_account(env.state, target).code
    else:
        raise TypeError()

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
    )
