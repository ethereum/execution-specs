"""
Test_static_callcallcodecallcode_011_oogm_after2.

Ported from:
state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfter2Filler.json
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
    [
        "state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfter2Filler.json"  # noqa: E501
    ],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_callcallcodecallcode_011_oogm_after2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcallcodecallcode_011_oogm_after2."""
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
    # {  [[ 0 ]] (STATICCALL 60150 (CALLDATALOAD 0) 0 64 0 64 ) [[ 1 ]] 1 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0xEAF6,
                address=Op.CALLDATALOAD(offset=0x0),
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
        address=Address(0x652A62E8338E91A46AA8387A2C205F35F79347AB),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 40080 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) (SSTORE 3 1) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALLCODE(
                gas=0x9C90,
                address=0x25D69E6A677BD6D872F436BAD807C3244A268673,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x3, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x0973E7675CA57F8E6DEB10CC07DE5D8B53956212),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 40080 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALLCODE(
                gas=0x9C90,
                address=0x25D69E6A677BD6D872F436BAD807C3244A268673,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x40, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x24)
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
        address=Address(0x13A5EB6FC2CF111FBA5DE5C336A9510E8229A44C),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 20020 <contract:0x1000000000000000000000000000000000000003> 0 0 64 0 64 ) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x4E34,
            address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
            value=0x0,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x25D69E6A677BD6D872F436BAD807C3244A268673),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0x335C5531B84765A7626E6E76688F18B81BE5259C),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_2, left_padding=True),
    ]
    tx_gas = [172000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {target: Account(storage={0: 0, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
