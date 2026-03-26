"""
call -> call -> oog callcode -> code 

Ported from:
state_tests/stCallCodes/callcallcallcode_001_OOGMBeforeFiller.json
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
    ["state_tests/stCallCodes/callcallcallcode_001_OOGMBeforeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcallcode_001_oogm_before(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """call -> call -> oog callcode -> code """
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
    # {  [[ 0 ]] (CALL 800000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0xc3500, address=0x471072d55a5a95044c2326f0e94a6d8df5b8089e, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x335b558774699d81f685543cfbcde5c4e5407686"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (CALL 600000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) [[11]] 1 }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.CALL(gas=0x927c0, address=0xd33ab78ac3965e7d6f9548dff5839138a9f69c5, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0xb, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x471072d55a5a95044c2326f0e94a6d8df5b8089e"),  # noqa: E501
    )
    # Source: lll
    # { (KECCAK256 0x00 0x2fffff) [[ 2 ]] (CALLCODE 400000 <contract:0x1000000000000000000000000000000000000003> 0 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.POP(Op.SHA3(offset=0x0, size=0x2fffff))
        + Op.SSTORE(key=0x2, value=Op.CALLCODE(gas=0x61a80, address=0xb126c622075b1189fb6c45e851641cfaddf65b36, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0x0d33ab78ac3965e7d6f9548dff5839138a9f69c5"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xb126c622075b1189fb6c45e851641cfaddf65b36"),  # noqa: E501
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
        addr_0x1000000000000000000000000000000000000003: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
