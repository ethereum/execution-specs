"""
test_call_then_call_value_fail_then_returndatasize

Ported from:
state_tests/stReturnDataTest/call_then_call_value_fail_then_returndatasizeFiller.json
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
    ["state_tests/stReturnDataTest/call_then_call_value_fail_then_returndatasizeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_then_call_value_fail_then_returndatasize(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_then_call_value_fail_then_returndatasize"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x834185262e53584684bf2b72c64e510013c235d0f45e462db65900455df45a35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    # Source: lll
    # { (seq (MSTORE 0 0x0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff) (RETURN 0 32)) }
    addr_0x0aabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x111122223333444455556666777788889999aaaabbbbccccddddeeeeffff)
        + Op.RETURN(offset=0x0, size=0x20) + Op.STOP,
        nonce=0,
        address=Address("0x9898dd5e5c526b55ec49b1047e298705c13279f1"),  # noqa: E501
    )
    # Source: lll
    # { (seq (CALL 0x0900000000 <contract:0x0aabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6> 0 0 0 0 0x20) (CALL 0x0900000000 <contract:0x0aabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6> 0xffffffffffff 0 0 0 0x20) (SSTORE 0 (RETURNDATASIZE)) )}
    target = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x900000000, address=0x9898dd5e5c526b55ec49b1047e298705c13279f1, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x20))
        + Op.POP(Op.CALL(gas=0x900000000, address=0x9898dd5e5c526b55ec49b1047e298705c13279f1, value=0xffffffffffff, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x20))
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE) + Op.STOP,
        storage={0: 1},
        nonce=0,
        address=Address("0x0e496b29ad2f0e55adf292c08a6a9289cb163835"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=100000,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
