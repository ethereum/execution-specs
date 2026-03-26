"""
call -> call -> code oog 

Ported from:
state_tests/stCallCodes/callcall_00_OOGEFiller.json
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
    ["state_tests/stCallCodes/callcall_00_OOGEFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcall_00_ooge(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """call -> call -> code oog """
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (CALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0x249f0, address=0x9196f97bca1b117e521275693c79420479d9cc90, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x4353e77718be108d4c149d88b34caceda42c5c66"),  # noqa: E501
    )
    # Source: lll
    # { [[ 1 ]] (CALL 20020 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) [[11]] 1 }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.CALL(gas=0x4e34, address=0x766b2cf0691f51029181fc511395b7ab71353a88, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0xb, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x9196f97bca1b117e521275693c79420479d9cc90"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 2 1) (KECCAK256 0x00 0x2fffff) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x1) + Op.SHA3(offset=0x0, size=0x2fffff)
        + Op.STOP,
        nonce=0,
        address=Address("0x766b2cf0691f51029181fc511395b7ab71353a88"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=1000000,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={0: 1}),
        addr_0x1000000000000000000000000000000000000001: Account(storage={11: 1}),
        addr_0x1000000000000000000000000000000000000002: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
