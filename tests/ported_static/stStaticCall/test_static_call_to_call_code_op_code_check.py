"""
test_static_call_to_call_code_op_code_check

Ported from:
state_tests/stStaticCall/static_callToCallCodeOpCodeCheckFiller.json
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
    ["state_tests/stStaticCall/static_callToCallCodeOpCodeCheckFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_call_to_call_code_op_code_check(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_call_to_call_code_op_code_check"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 100000 (CALLDATALOAD 0) 0 0 0 0)  }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x186a0, address=Op.CALLDATALOAD(offset=0x0), args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x7ef8271e6cdb0a23220b73bf3e9697e173f9d015"),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 (CALLCODE 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0 0)) (if (= 1 (MLOAD 0)) (MSTORE 1 1) (SSTORE 1 1) ) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLCODE(gas=0x186a0, address=0xf0d7d1b32bbc0012f183fb3e3f4f9434abed93bd, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.JUMPI(pc=0x38, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=0x1, value=0x1) + Op.JUMP(pc=0x3e) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xea435169b5c0848d55c71080fb937e9b611a505d"),  # noqa: E501
    )
    # Source: lll
    # {  (if (= <eoa:sender:0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b> (ORIGIN)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x1000000000000000000000000000000000000001> (CALLER)) (MSTORE 1 1) (SSTORE 1 2) ) (if (= <contract:0x1000000000000000000000000000000000000001> (ADDRESS)) (MSTORE 1 1) (SSTORE 1 2) )   (if (= 0 (CALLVALUE)) (MSTORE 1 1) (SSTORE 1 2) )        }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.JUMPI(pc=0x22, condition=Op.EQ(0xebaf50debf10e08302fe4280c32df010463ca297, Op.ORIGIN))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x28) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x4b, condition=Op.EQ(0xea435169b5c0848d55c71080fb937e9b611a505d, Op.CALLER))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x51) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x74, condition=Op.EQ(0xea435169b5c0848d55c71080fb937e9b611a505d, Op.ADDRESS))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x7a) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST
        + Op.JUMPI(pc=0x8a, condition=Op.EQ(0x0, Op.CALLVALUE))
        + Op.SSTORE(key=0x1, value=0x2) + Op.JUMP(pc=0x90) + Op.JUMPDEST
        + Op.MSTORE(offset=0x1, value=0x1) + Op.JUMPDEST + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xf0d7d1b32bbc0012f183fb3e3f4f9434abed93bd"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("000000000000000000000000ea435169b5c0848d55c71080fb937e9b611a505d"),  # noqa: E501
        gas_limit=1000000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
