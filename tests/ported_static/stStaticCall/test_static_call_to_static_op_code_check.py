"""
Test_static_call_to_static_op_code_check.

Ported from:
state_tests/stStaticCall/static_callToStaticOpCodeCheckFiller.json
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callToStaticOpCodeCheckFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_call_to_static_op_code_check(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_to_static_op_code_check."""
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
        gas_limit=10000000,
    )

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 100000 (CALLDATALOAD 0) 0 0 0 0)  }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x186A0,
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
        address=Address(0x7EF8271E6CDB0A23220B73BF3E9697E173F9D015),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 (STATICCALL 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0)) (if (= 1 (MLOAD 0)) (MSTORE 1 1) (SSTORE 1 1) ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=Op.STATICCALL(
                gas=0x186A0,
                address=0xD366057A988CB6562F7FA2A601F06A503D30A90,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPI(pc=0x36, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.JUMP(pc=0x3C)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x5E93BF4D3E4A5F90AE3A7A68DBD03E6C47F1245A),  # noqa: E501
    )
    # Source: lll
    # {  (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x1000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x1000000000000000000000000000000000000002> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) )        }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x22,
            condition=Op.EQ(
                0xEBAF50DEBF10E08302FE4280C32DF010463CA297, Op.ORIGIN
            ),
        )
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x28)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x4B,
            condition=Op.EQ(
                0x5E93BF4D3E4A5F90AE3A7A68DBD03E6C47F1245A, Op.CALLER
            ),
        )
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x51)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x74,
            condition=Op.EQ(
                0xD366057A988CB6562F7FA2A601F06A503D30A90, Op.ADDRESS
            ),
        )
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x7A)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
        + Op.SSTORE(key=0x1, value=0x2)
        + Op.JUMP(pc=0x90)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x0D366057A988CB6562F7FA2A601F06A503D30A90),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Hash(addr, left_padding=True),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
