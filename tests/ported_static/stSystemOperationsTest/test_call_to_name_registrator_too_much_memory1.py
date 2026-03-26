"""
test_call_to_name_registrator_too_much_memory1

Ported from:
state_tests/stSystemOperationsTest/CallToNameRegistratorTooMuchMemory1Filler.json
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
    ["state_tests/stSystemOperationsTest/CallToNameRegistratorTooMuchMemory1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_to_name_registrator_too_much_memory1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_to_name_registrator_too_much_memory1"""
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
        gas_limit=10000000,
    )

    # Source: lll
    # { (MSTORE 0 0xeeffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00) (MSTORE 32 0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa ) [[ 0 ]] (CALL 500 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 23 0 9865432 64 0) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0xeeffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00)
        + Op.MSTORE(offset=0x20, value=0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa)
        + Op.SSTORE(key=0x0, value=Op.CALL(gas=0x1f4, address=0x15eb18969e0925c8e4a76fd7cbce36a2b056b27e, value=0x17, args_offset=0x0, args_size=0x9688d8, ret_offset=0x40, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x375d9c49dd17c920398b81ba030bf150bc16af59"),  # noqa: E501
    )
    # Source: raw
    # 0x6000355415600957005b60203560003555
    addr_0x945304eb96065b2a98b57a48a06ae28d285a71b5 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x9, condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))))  # noqa: E501
        + Op.STOP + Op.JUMPDEST
        + Op.SSTORE(key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)),  # noqa: E501
        balance=23,
        nonce=0,
        address=Address("0x15eb18969e0925c8e4a76fd7cbce36a2b056b27e"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=300000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={}, nonce=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
