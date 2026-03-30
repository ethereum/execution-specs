"""
Test_static_log_caller.

Ported from:
state_tests/stStaticCall/static_log_CallerFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_log_CallerFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_log_caller(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_log_caller."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { [[ 0 ]] (STATICCALL 50000 (CALLDATALOAD 0) 0 0 0 0) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0xC350,
                address=Op.CALLDATALOAD(offset=0x0),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xD8C1FCDB2990F08E5FE821BF5AF85F34201BA79A),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE8 0 0xff) (LOG0 0 32 ) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0xFF)
        + Op.LOG0(offset=0x0, size=0x20)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xC725ABAE869E29A5448DCA5B51A58F0C960D4069),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE8 0 0xff) (LOG1 0 32 (CALLER) ) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0xFF)
        + Op.LOG1(offset=0x0, size=0x20, topic_1=Op.CALLER)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x842936958D62030200FBCEF4371460D8A9400D05),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE8 0 0xff) (LOG2 0 32 0 (CALLER) ) }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0xFF)
        + Op.LOG2(offset=0x0, size=0x20, topic_1=0x0, topic_2=Op.CALLER)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x861CCCBD560D81A33AAC05190E986540663C6BBA),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE8 0 0xff) (LOG3 0 32 0 0 (CALLER) ) }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0xFF)
        + Op.LOG3(
            offset=0x0, size=0x20, topic_1=0x0, topic_2=0x0, topic_3=Op.CALLER
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x6C5DA6457F756A77C392C72FE884F7F650428AEF),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE8 0 0xff) (LOG4 0 32 0 0 0 (CALLER) )}
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE8(offset=0x0, value=0xFF)
        + Op.LOG4(
            offset=0x0,
            size=0x20,
            topic_1=0x0,
            topic_2=0x0,
            topic_3=0x0,
            topic_4=Op.CALLER,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x586CFAA42DB8B743452A87549943AC07A09DE5CC),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
        Hash(addr_4, left_padding=True),
        Hash(addr_5, left_padding=True),
    ]
    tx_gas = [210000]
    tx_value = [100000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {target: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
