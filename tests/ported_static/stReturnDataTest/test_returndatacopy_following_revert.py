"""
test_returndatacopy_following_revert

Ported from:
state_tests/stReturnDataTest/returndatacopy_following_revertFiller.json
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
    ["state_tests/stReturnDataTest/returndatacopy_following_revertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_following_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_returndatacopy_following_revert"""
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
    # { (seq (MSTORE 0 0x0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff) (REVERT 0 32)) }
    addr_0x0aabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x111122223333444455556666777788889999aaaabbbbccccddddeeeeffff)
        + Op.REVERT(offset=0x0, size=0x20) + Op.STOP,
        nonce=0,
        address=Address("0x2159735ba26480adc67f0ee9d4a05e5405a5cf83"),  # noqa: E501
    )
    # Source: lll
    # { (seq (CALL 0x0900000000 <contract:0x0aabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6> 0 0 0 0 0) (RETURNDATACOPY 0 0 32) (SSTORE 0 (MLOAD 0)) )}
    target = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x900000000, address=0x2159735ba26480adc67f0ee9d4a05e5405a5cf83, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0)) + Op.STOP,
        storage={0: 1},
        nonce=0,
        address=Address("0x2faf9d2a81304665c9a06a42935ddc42b24f488b"),  # noqa: E501
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

    post = {
        target: Account(
                storage={
            0: 0x111122223333444455556666777788889999aaaabbbbccccddddeeeeffff,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
