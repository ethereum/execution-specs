"""
test_static_revert_depth2

Ported from:
state_tests/stStaticCall/static_RevertDepth2Filler.json
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
    ["state_tests/stStaticCall/static_RevertDepth2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_revert_depth2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_revert_depth2"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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
    # { [[0]] (ADD 1 (SLOAD 0)) [[1]] (STATICCALL 150000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0) [[2]] (STATICCALL 150000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0)}
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
        + Op.SSTORE(key=0x1, value=Op.STATICCALL(gas=0x249f0, address=0x5dd18f4768e54de1443f70ec11ad95d5db424293, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=Op.STATICCALL(gas=0x249f0, address=0xa61140a1c2699a13c619940208a513d42f654e98, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0x57c111943c5e6f1817ee85fd1212409b7d1f7f26"),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0) (MSTORE 1 1) }
    addr_0xb000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=0xc350, address=0x15b1327fe926a2172adfd10efdef1505c8e15461, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x5dd18f4768e54de1443f70ec11ad95d5db424293"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 1 1) }
    addr_0xc000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x15b1327fe926a2172adfd10efdef1505c8e15461"),  # noqa: E501
    )
    # Source: lll
    # { (STATICCALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0) (KECCAK256 0x00 0x2fffff) }
    addr_0xd000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=0xc350, address=0x15b1327fe926a2172adfd10efdef1505c8e15461, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SHA3(offset=0x0, size=0x2fffff) + Op.STOP,
        nonce=0,
        address=Address("0xa61140a1c2699a13c619940208a513d42f654e98"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=1706850,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={0: 1, 1: 1, 2: 0}),
        addr_0xb000000000000000000000000000000000000000: Account(storage={0: 0, 1: 0}),
        addr_0xc000000000000000000000000000000000000000: Account(storage={0: 0}),
        addr_0xd000000000000000000000000000000000000000: Account(storage={0: 0, 1: 0, 2: 0}),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
