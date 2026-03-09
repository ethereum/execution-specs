"""
call -> call -> oog call -> code.

Ported from:
tests/static/state_tests/stCallCodes/callcallcall_000_OOGMBeforeFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCallCodes/callcallcall_000_OOGMBeforeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcall_000_oogm_before(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Call -> call -> oog call -> code."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: LLL
    # {  [[ 0 ]] (CALL 800000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0xC3500,
                    address=0x471072D55A5A95044C2326F0E94A6D8DF5B8089E,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x335b558774699d81f685543cfbcde5c4e5407686"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=0x927C0,
                    address=0x51A61D678EC27711369C527E5D42A9DE66A5727F,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0xB, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x471072d55a5a95044c2326f0e94a6d8df5b8089e"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.POP(Op.SHA3(offset=0x0, size=0x2FFFFF))
            + Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=0x61A80,
                    address=0xB126C622075B1189FB6C45E851641CFADDF65B36,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x51a61d678ec27711369c527e5d42a9de66a5727f"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xb126c622075b1189fb6c45e851641cfaddf65b36"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1000000,
    )

    post = {
        contract: Account(storage={0: 1}),
        callee: Account(storage={11: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
