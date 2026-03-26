"""
test_call_one_v_call_suicide2

Ported from:
state_tests/stEIP158Specific/CALL_OneVCallSuicide2Filler.json
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
    ["state_tests/stEIP158Specific/CALL_OneVCallSuicide2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_one_v_call_suicide2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_one_v_call_suicide2"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    addr_0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")  # noqa: E501
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
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

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { [0](GAS) (CALL 60000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 0 0 0) [[100]] (SUB @0 (GAS)) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.CALL(gas=0xea60, address=0x99378e0db04e57ae174ad69770e1b7a0aa805930, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x64, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        balance=100,
        nonce=0,
        address=Address("0xea04224539257fbe043981aa6058fbc1d5e21b1a"),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <eoa:0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }
    addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0xeb201d2887816e041f6e807e804f64f3a7a226fe)
        + Op.STOP,
        nonce=0,
        address=Address("0x99378e0db04e57ae174ad69770e1b7a0aa805930"),  # noqa: E501
    )
    pre[addr_0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b] = Account(balance=0, nonce=1)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=600000,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}, balance=0),
        target: Account(storage={100: 16937}, balance=99),
        addr_0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(balance=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
