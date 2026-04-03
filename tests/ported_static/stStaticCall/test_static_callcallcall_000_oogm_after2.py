"""
Test_static_callcallcall_000_oogm_after2.

Ported from:
state_tests/stStaticCall/static_callcallcall_000_OOGMAfter2Filler.json
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
    ["state_tests/stStaticCall/static_callcallcall_000_OOGMAfter2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_callcallcall_000_oogm_after2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcallcall_000_oogm_after2."""
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
    # {  [[ 0 ]] (STATICCALL 700000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 111 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0xAAE60,
                address=0x10345562E309B2045C737FFDD46E941710495FC4,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x6F, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x6DE4E4FA82A7139E6804B5B47B42E366A9595946),  # noqa: E501
    )
    # Source: lll
    # {   (MSTORE 3 1) (STATICCALL 450000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)  ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x6DDD0,
                address=0xA34EEE061F267A63C872265BED51C483F777A7B0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x44, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x28)
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
        address=Address(0x10345562E309B2045C737FFDD46E941710495FC4),  # noqa: E501
    )
    # Source: lll
    # {   (MSTORE 3 1) (STATICCALL 120020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 )  (MSTORE 32 1)}  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x1D4D4,
                address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xA34EEE061F267A63C872265BED51C483F777A7B0),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0x335C5531B84765A7626E6E76688F18B81BE5259C),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1720000,
    )

    post = {
        target: Account(storage={0: 0, 1: 0, 2: 0, 3: 0, 111: 1}),
        addr: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_2: Account(storage={2: 0, 3: 0}),
        addr_3: Account(storage={3: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
