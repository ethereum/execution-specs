"""
Test_revert_depth2.

Ported from:
state_tests/stRevertTest/RevertDepth2Filler.json
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
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertDepth2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_depth2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_revert_depth2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { [[0]] (ADD 1 (SLOAD 0)) [[1]] (CALL 150000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0 0) [[2]] (CALL 150000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0 0)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0x249F0,
                address=0x707F29673F05E46FEEB7C4766419A222010AE45,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x249F0,
                address=0x78ED2EB0809CD080C7837DC83AFC388A2B98D200,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x68EA09E164A8B66DE117A2C306B3966E6D71CA93),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (ADD 1 (SLOAD 0)) [[1]] (CALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0 0)}  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0xC350,
                address=0xC47BCBF49DD735566CFDE927821E938D5B33014C,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x0707F29673F05E46FEEB7C4766419A222010AE45),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (ADD 1 (SLOAD 0)) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
        + Op.STOP,
        nonce=0,
        address=Address(0xC47BCBF49DD735566CFDE927821E938D5B33014C),  # noqa: E501
    )
    # Source: lll
    # { [[0]] (ADD 1 (SLOAD 0)) [[1]] (CALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0 0) [[2]] (GAS)}  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0xC350,
                address=0xC47BCBF49DD735566CFDE927821E938D5B33014C,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=Op.GAS)
        + Op.STOP,
        nonce=0,
        address=Address(0x78ED2EB0809CD080C7837DC83AFC388A2B98D200),  # noqa: E501
    )

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [170685, 136685]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {
        target: Account(storage={0: 0, 1: 0, 2: 0}),
        addr: Account(storage={0: 0, 1: 0}),
        addr_2: Account(storage={0: 0}),
        addr_3: Account(storage={0: 0, 1: 0, 2: 0}),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
