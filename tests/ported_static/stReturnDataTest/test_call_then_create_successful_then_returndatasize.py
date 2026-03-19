"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stReturnDataTest
call_then_create_successful_then_returndatasizeFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stReturnDataTest/call_then_create_successful_then_returndatasizeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_then_create_successful_then_returndatasize(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x834185262E53584684BF2B72C64E510013C235D0F45E462DB65900455DF45A35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF,  # noqa: E501
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.STOP
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x24b406508240d6f2783499d1fd65fedd0feeef37"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)
    # Source: LLL
    # { (seq (CALL 0x0900000000 <contract:0x0aabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6> 0 0 0 0 0) (CREATE 0 0 (lll (seq (mstore 0 0x112233) (RETURN 0 32) (STOP) ) 0)) (SSTORE 0 (RETURNDATASIZE)) (STOP) )}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x900000000,
                    address=0x24B406508240D6F2783499D1FD65FEDD0FEEEF37,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.PUSH1[0xE]
            + Op.CODECOPY(dest_offset=0x0, offset=0x3C, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.CREATE)
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.STOP
            + Op.STOP
            + Op.INVALID
            + Op.MSTORE(offset=0x0, value=0x112233)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.STOP
            + Op.STOP
        ),
        storage={0x0: 0x1},
        nonce=0,
        address=Address("0xcc5fbabb1e86f7744ed4840b4153736d3c0ae2a2"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "7d111122223333444455556666777788889999aaaabbbbccccddddeeeeffff60005260206000f30000"  # noqa: E501
                    )
                ),
                Address("0x9ad81872d43eab9c434b755513337c6b53ac1b0a"): Account(
                    code=bytes.fromhex(
                        "0000000000000000000000000000000000000000000000000000000000112233"  # noqa: E501
                    )
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060007324b406508240d6f2783499d1fd65fedd0feeef37640900000000f150600e80603c60003960006000f0503d6000550000fe6211223360005260206000f30000"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
