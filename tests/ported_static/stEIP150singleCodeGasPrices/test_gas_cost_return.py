"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP150singleCodeGasPrices/gasCostReturnFiller.yml
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
    ["state_tests/stEIP150singleCodeGasPrices/gasCostReturnFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_gas_cost_return(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE)

    # Source: raw
    # 0x600060FF00
    addr = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.PUSH1[0xFF] + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: raw
    # 0x600060FFF3
    addr_2 = pre.deploy_contract(
        code=Op.RETURN(offset=0xFF, size=0x0),
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Initialization
    #
    #   ; Variables (0x20 byte wide)
    #   (def 'gasB4         0x000)  ; Before the action being measured
    #
    #   ; Gas for the STOP call
    #   (def 'gasSTOP       0x020)
    #
    #   ; Gas for the RETURN call
    #   (def 'gasRETURN     0x040)
    #
    #   ; Play with the variables here to avoid having the memory allocation
    #   ; affect the gas calculation
    #   [gasB4] 0x60A7
    #   [gasSTOP] 0x60A7
    #   [gasRETURN] 0x60A7
    #
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Run the operation
    #
    #   [gasB4] (gas)
    #   (call 0x10000 0x1000 0 0 0 0 0)
    #   [gasSTOP] (- @gasB4 (gas))
    #
    #
    #   [gasB4] (gas)
    #   (call 0x10000 0x2000 0 0 0 0 0)
    #   [gasRETURN] (- @gasB4 (gas))
    # ... (11 more lines)
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x60A7)
        + Op.MSTORE(offset=0x20, value=0x60A7)
        + Op.MSTORE(offset=0x40, value=0x60A7)
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x20, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x40, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.SSTORE(
            key=0x0, value=Op.SUB(Op.MLOAD(offset=0x20), Op.MLOAD(offset=0x40))
        )
        + Op.STOP,
        storage={0: 24743},
        balance=0xBA1A9CE0BA1A9CE,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=16777216,
        value=1,
    )

    post = {target: Account(storage={0: 0, 1: 0})}

    state_test(pre=pre, post=post, tx=tx)
