"""
Test_static_callcallcodecallcode_011_suicide_middle.

Ported from:
state_tests/stStaticCall/static_callcallcodecallcode_011_SuicideMiddleFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_callcallcodecallcode_011_SuicideMiddleFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecallcode_011_suicide_middle(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcallcodecallcode_011_suicide_middle."""
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
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x249F0,
                address=0x92D7028788CAA240253B7B2A92386464690CDC72,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x569CDC3B32CC3F9747BBDE39FD70FEAD591D2F0D),  # noqa: E501
    )
    # Source: lll
    # {  (DELEGATECALL 100000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=0x186A0,
            address=0xECA01D36DBE4F4AB283A49016EFA370BAC7E7346,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x92D7028788CAA240253B7B2A92386464690CDC72),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <contract:target:0x1000000000000000000000000000000000000000>) (DELEGATECALL 50000 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0x569CDC3B32CC3F9747BBDE39FD70FEAD591D2F0D
        )
        + Op.DELEGATECALL(
            gas=0xC350,
            address=0x48E2D4C0B593BFEBE5DDB4F13AA355B8BD83DDD3,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0xECA01D36DBE4F4AB283A49016EFA370BAC7E7346),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x48E2D4C0B593BFEBE5DDB4F13AA355B8BD83DDD3),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {
        target: Account(storage={0: 1, 1: 1}),
        addr_2: Account(balance=0x2540BE400),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
