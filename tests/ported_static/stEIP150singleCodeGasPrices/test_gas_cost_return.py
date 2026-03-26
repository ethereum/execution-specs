"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/stEIP150singleCodeGasPrices/gasCostReturnFiller.yml
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
    ["state_tests/stEIP150singleCodeGasPrices/gasCostReturnFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_gas_cost_return(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x40ac0fc28c27e961ee46ec43355a094de205856edbd4654cf2577c2608d4ec1e
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw
    # 0x600060FF00
    addr_0x0000000000000000000000000000000000001000 = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.PUSH1[0xff] + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0xeb0e68b88a12fc84ad4a1eeb07b289638c4d9f3c"),  # noqa: E501
    )
    # Source: raw
    # 0x600060FFF3
    addr_0x0000000000000000000000000000000000002000 = pre.deploy_contract(
        code=Op.RETURN(offset=0xff, size=0x0),
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x35cd99e56b0f9ac243172a86bef4d042dfdbc166"),  # noqa: E501
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
        code=Op.MSTORE(offset=0x0, value=0x60a7)
        + Op.MSTORE(offset=0x20, value=0x60a7)
        + Op.MSTORE(offset=0x40, value=0x60a7)
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.CALL(gas=0x10000, address=0x1000, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.MSTORE(offset=0x20, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.CALL(gas=0x10000, address=0x2000, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.MSTORE(offset=0x40, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.SSTORE(key=0x0, value=Op.SUB(Op.MLOAD(offset=0x20), Op.MLOAD(offset=0x40)))  # noqa: E501
        + Op.STOP,
        storage={0: 24743},
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x155665fb22995bb5b9dc1d8d9d57a00ac64dc1e0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xba1a9ce0ba1a9ce)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("00"),
        gas_limit=16777216,
        value=1,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={0: 0, 1: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
