"""
Test_static_callcodecallcodecall_110_oogm_after_2.

Ported from:
state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMAfter_2Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMAfter_2Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_static_callcodecallcodecall_110_oogm_after_2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcodecallcodecall_110_oogm_after_2."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {  (MSTORE 3 1) }
    addr_3 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
    )
    # Source: lll
    # { (STATICCALL 20020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(
        code=Op.STATICCALL(
            gas=0x4E34,
            address=addr_3,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
    )
    # Source: lll
    # {  (DELEGATECALL 40080 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.POP(
            Op.DELEGATECALL(
                gas=0x9C90,
                address=Op.PUSH20[addr_2],
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x3E, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x22)
        + Op.JUMPDEST
        + Op.STOP,
    )
    # Source: lll
    # {  [[ 0 ]] (DELEGATECALL 60150 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0xEAF6,
                address=addr,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
    )

    post = {target: Account(storage={0: 0, 1: 1})}

    state_test(pre=pre, post=post, tx=tx)
