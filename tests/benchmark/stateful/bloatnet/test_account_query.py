"""
Benchmark operations that require querying the account state, either on the
current executing account or on a target account.

Supported Opcodes:
- SELFBALANCE
- CODESIZE
- CODECOPY
- EXTCODESIZE
- EXTCODEHASH
- EXTCODECOPY
- BALANCE
"""

from typing import Any

import pytest
from execution_testing import (
    Account,
    Alloc,
    BenchmarkTestFiller,
    JumpLoopGenerator,
    Op,
)


@pytest.mark.repricing(
    empty_code=True,
    initial_balance=True,
    initial_storage=True,
)
@pytest.mark.parametrize(
    "opcode",
    [
        Op.BALANCE,
        Op.EXTCODESIZE,
        Op.EXTCODEHASH,
        Op.CALL,
        Op.CALLCODE,
        Op.DELEGATECALL,
        Op.STATICCALL,
    ],
)
@pytest.mark.parametrize(
    "empty_code",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "initial_balance",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "initial_storage",
    [
        True,
        False,
    ],
)
def test_ext_account_query_warm(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    opcode: Op,
    empty_code: bool,
    initial_balance: bool,
    initial_storage: bool,
) -> None:
    """
    Test running a block with as many stateful opcodes doing warm access
    for an account.
    """
    # Setup
    post = {}

    # Case 1: Completely empty account (no balance, no storage, no code)
    if not initial_balance and not initial_storage and empty_code:
        target_addr = pre.nonexistent_account()
    # Case 2: EOA with optional balance and storage
    elif empty_code:
        eoa_kwargs: dict[str, Any] = {}
        if initial_balance:
            eoa_kwargs["amount"] = 100
        if initial_storage:
            eoa_kwargs["storage"] = {0: 0x1337}
        target_addr = pre.fund_eoa(**eoa_kwargs)
    # Case 3: Contract with optional balance and storage
    else:
        contract_kwargs: dict[str, Any] = {"code": Op.STOP + Op.JUMPDEST * 100}
        if initial_balance:
            contract_kwargs["balance"] = 100
        if initial_storage:
            contract_kwargs["storage"] = {0: 0x1337}
        target_addr = pre.deploy_contract(**contract_kwargs)
        post[target_addr] = Account(**contract_kwargs)

    benchmark_test(
        target_opcode=opcode,
        post=post,
        code_generator=JumpLoopGenerator(
            setup=Op.MSTORE(0, target_addr),
            attack_block=Op.POP(opcode(address=Op.MLOAD(0))),
        ),
    )
