"""
test_call_then_create2_successful_then_returndatasize

Ported from:
state_tests/stCreate2/call_then_create2_successful_then_returndatasizeFiller.json
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
    ["state_tests/stCreate2/call_then_create2_successful_then_returndatasizeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_then_create2_successful_then_returndatasize(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_then_create2_successful_then_returndatasize"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x0aabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6")
    contract_1 = Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=47244640256,
    )

    # Source: lll
    # { (seq (MSTORE 0 0x0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff) (RETURN 0 32) (STOP) ) }
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x111122223333444455556666777788889999aaaabbbbccccddddeeeeffff)
        + Op.RETURN(offset=0x0, size=0x20) + Op.STOP * 2,
        nonce=0,
        address=Address("0x0aabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6"),  # noqa: E501
    )
    # Source: lll
    # { (seq (CALL 0x0900000000 0x0aabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6 0 0 0 0 0) (CREATE2 0 0 (lll (seq (mstore 0 0x112233) (RETURN 0 32) (STOP) ) 0) 0) (SSTORE 0 (RETURNDATASIZE)) (STOP) )}
    contract_1 = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x900000000, address=0xaabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.PUSH1[0x0] + Op.PUSH1[0xe]
        + Op.CODECOPY(dest_offset=0x0, offset=0x3e, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.POP(Op.CREATE2)
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE) + Op.STOP * 2 + Op.INVALID  # noqa: E501
        + Op.MSTORE(offset=0x0, value=0x112233)
        + Op.RETURN(offset=0x0, size=0x20) + Op.STOP * 2,
        storage={0: 1},
        nonce=0,
        address=Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)


    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=b'',
        gas_limit=100000,
        nonce=0,
        gas_price=10,
    )

    post = {
        Address("0xc0c06666fad9e52251740536e21fc0f3db0e0fa0"): Account(
                code=bytes.fromhex("0000000000000000000000000000000000000000000000000000000000112233"),  # noqa: E501
            ),
        contract_1: Account(storage={0: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
