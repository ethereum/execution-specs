"""
Test_static_callcallcallcode_001_ooge.

Ported from:
state_tests/stStaticCall/static_callcallcallcode_001_OOGEFiller.json
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
    ["state_tests/stStaticCall/static_callcallcallcode_001_OOGEFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_callcallcallcode_001_ooge(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcallcallcode_001_ooge."""
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
    # {  [[ 0 ]] (STATICCALL 600000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) (MSTORE 3 1)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x927C0,
                address=0x6F80B859BA9392B2C26E5930C330D4A7247FBA4F,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.MSTORE(offset=0x3, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x563F06D1277F7CB092689AC2168D6EECD1ACB499),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 3 1) (STATICCALL 300000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (MSTORE 3 1)}  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=0xA3E14608664E4A0229F96C49500F83F0FDBF3DCB,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x3, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x6F80B859BA9392B2C26E5930C330D4A7247FBA4F),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (DELEGATECALL 120020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 3 1)}  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x1D4D4,
                address=0xE574F7EC5305BE91332B5B8B12DEB8966E05F42D,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x3, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xA3E14608664E4A0229F96C49500F83F0FDBF3DCB),  # noqa: E501
    )
    # Source: lll
    # {  (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)  )}
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1C, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
        address=Address(0xE574F7EC5305BE91332B5B8B12DEB8966E05F42D),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1720000,
    )

    post = {
        target: Account(storage={0: 1, 2: 0, 3: 0}),
        addr: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_2: Account(storage={2: 0, 3: 0}),
        addr_3: Account(storage={3: 0}),
        sender: Account(storage={1: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
