"""
call -> callcode -> call -> code, params check

Ported from:
state_tests/stCallCodes/callcallcodecall_010Filler.json
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
    ["state_tests/stCallCodes/callcallcodecall_010Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcodecall_010(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """call -> callcode -> call -> code, params check"""
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
    # {  [[ 0 ]] (CALL 350000 <contract:0x1000000000000000000000000000000000000001> 1 0 64 0 64 ) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0x55730, address=0x4c0de71b93de6b7055a3686e4bf93add02b39ed8, value=0x1, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xeb09ff15547417853f6f4b240b8804769c37b0f1"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (CALLCODE 300000 <contract:0x1000000000000000000000000000000000000002> 2 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.CALLCODE(gas=0x493e0, address=0x62441cbe78aa4a4244e084d4f86098e31dced749, value=0x2, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x4c0de71b93de6b7055a3686e4bf93add02b39ed8"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 2 ]] (CALL 250000 <contract:0x1000000000000000000000000000000000000003> 3 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=Op.CALL(gas=0x3d090, address=0x7e63847aad8ca50fb7c04777dce6871a6bf8de0c, value=0x3, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x62441cbe78aa4a4244e084d4f86098e31dced749"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) (SSTORE 4 (CALLER)) (SSTORE 7 (CALLVALUE)) (SSTORE 330 (ADDRESS)) (SSTORE 332 (ORIGIN)) (SSTORE 336 (CALLDATASIZE)) (SSTORE 338 (CODESIZE)) (SSTORE 340 (GASPRICE)) }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.SSTORE(key=0x4, value=Op.CALLER)  # noqa: E501
        + Op.SSTORE(key=0x7, value=Op.CALLVALUE)
        + Op.SSTORE(key=0x14a, value=Op.ADDRESS)
        + Op.SSTORE(key=0x14c, value=Op.ORIGIN)
        + Op.SSTORE(key=0x150, value=Op.CALLDATASIZE)
        + Op.SSTORE(key=0x152, value=Op.CODESIZE)
        + Op.SSTORE(key=0x154, value=Op.GASPRICE) + Op.STOP,
        nonce=0,
        address=Address("0x7e63847aad8ca50fb7c04777dce6871a6bf8de0c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=3000000,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0x1000000000000000000000000000000000000001: Account(storage={1: 1, 2: 1}),
        addr_0x1000000000000000000000000000000000000003: Account(
                storage={
            3: 1,
            4: 0x4c0de71b93de6b7055a3686e4bf93add02b39ed8,
            7: 3,
            330: 0x7e63847aad8ca50fb7c04777dce6871a6bf8de0c,
            332: 0xebaf50debf10e08302fe4280c32df010463ca297,
            336: 64,
            338: 39,
            340: 10,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
