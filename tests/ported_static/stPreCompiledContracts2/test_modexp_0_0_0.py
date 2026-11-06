"""
Hash the MODEXP output for base 0, exponent 0 and modulus 0.

The contract calls MODEXP, copies the output through the identity
precompile and stores its hash. Each filler gives the execution a
different budget.

Ported from:
state_tests/stPreCompiledContracts2/modexp_0_0_0_20500Filler.json
state_tests/stPreCompiledContracts2/modexp_0_0_0_22000Filler.json
state_tests/stPreCompiledContracts2/modexp_0_0_0_25000Filler.json
state_tests/stPreCompiledContracts2/modexp_0_0_0_35000Filler.json

@manually-enhanced: Do not overwrite. An entry contract gives the
contract the filler's Cancun execution budget, shifted by the repricing
of the stored slot.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Cancun, Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Source: hex
# 0x600035601c52740100000000000000000000000000000000000000006020526fffffffffffffffffffffffffffffffff6040527fffffffffffffffffffffffffffffffff000000000000000000000000000000016060527402540be3fffffffffffffffffffffffffdabf41c006080527ffffffffffffffffffffffffdabf41c00000000000000000000000002540be40060a0526330c8d1da600051141561012b5760846004356004013511151558576004356004013560200160043560040161014037600161024061014051610160600060056305f5e0fff11558576001610220526102206021806102808284600060046015f150505061028080516020820120905060005561028060206020820352604081510160206001820306601f820103905060208203f350005b  # noqa: E501
CALLER_CODE = (
    Op.MSTORE(offset=0x1C, value=Op.CALLDATALOAD(offset=0x0))
    + Op.MSTORE(offset=0x20, value=0x10000000000000000000000000000000000000000)
    + Op.MSTORE(offset=0x40, value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    + Op.MSTORE(
        offset=0x60,
        value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000001,  # noqa: E501
    )
    + Op.MSTORE(offset=0x80, value=0x2540BE3FFFFFFFFFFFFFFFFFFFFFFFFFDABF41C00)
    + Op.MSTORE(
        offset=0xA0,
        value=0xFFFFFFFFFFFFFFFFFFFFFFFDABF41C00000000000000000000000002540BE400,  # noqa: E501
    )
    + Op.JUMPI(
        pc=0x12B,
        condition=Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x0), 0x30C8D1DA)),
    )
    + Op.JUMPI(
        pc=Op.PC,
        condition=Op.ISZERO(
            Op.ISZERO(
                Op.GT(
                    Op.CALLDATALOAD(
                        offset=Op.ADD(0x4, Op.CALLDATALOAD(offset=0x4))
                    ),
                    0x84,
                )
            )
        ),
    )
    + Op.CALLDATACOPY(
        dest_offset=0x140,
        offset=Op.ADD(0x4, Op.CALLDATALOAD(offset=0x4)),
        size=Op.ADD(
            0x20,
            Op.CALLDATALOAD(offset=Op.ADD(0x4, Op.CALLDATALOAD(offset=0x4))),
        ),
    )
    + Op.JUMPI(
        pc=Op.PC,
        condition=Op.ISZERO(
            Op.CALL(
                gas=0x5F5E0FF,
                address=0x5,
                value=0x0,
                args_offset=0x160,
                args_size=Op.MLOAD(offset=0x140),
                ret_offset=0x240,
                ret_size=0x1,
            )
        ),
    )
    + Op.MSTORE(offset=0x220, value=0x1)
    + Op.PUSH2[0x220]
    + Op.PUSH1[0x21]
    + Op.POP(
        Op.CALL(
            gas=0x15,
            address=0x4,
            value=0x0,
            args_offset=Op.DUP5,
            args_size=Op.DUP3,
            ret_offset=0x280,
            ret_size=Op.DUP1,
        )
    )
    + Op.POP * 2
    + Op.PUSH2[0x280]
    + Op.SHA3(offset=Op.ADD(Op.DUP3, 0x20), size=Op.MLOAD(offset=Op.DUP1))
    + Op.SWAP1
    + Op.POP
    + Op.PUSH1[0x0]
    + Op.SSTORE
    + Op.PUSH2[0x280]
    + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x20), value=0x20)
    + Op.ADD(Op.MLOAD(offset=Op.DUP2), 0x40)
    + Op.SUB(Op.ADD(Op.DUP3, 0x1F), Op.MOD(Op.SUB(Op.DUP3, 0x1), 0x20))
    + Op.SWAP1
    + Op.POP
    + Op.SUB(Op.DUP3, 0x20)
    + Op.RETURN
    + Op.POP
    + Op.STOP
    + Op.JUMPDEST
)

RESULT_HASH = (
    0xBC36789E7A1E281436464229828F817D6612F7B477D66591FF96A9E064BCC98A
)


@pytest.mark.ported_from(
    [
        "state_tests/stPreCompiledContracts2/modexp_0_0_0_20500Filler.json",
        "state_tests/stPreCompiledContracts2/modexp_0_0_0_22000Filler.json",
        "state_tests/stPreCompiledContracts2/modexp_0_0_0_25000Filler.json",
        "state_tests/stPreCompiledContracts2/modexp_0_0_0_35000Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "execution_budget, success",
    [
        pytest.param(20812, False, id="20500"),
        pytest.param(26408, True, id="22000"),
        pytest.param(25312, True, id="25000"),
        pytest.param(35312, True, id="35000"),
        pytest.param(None, True, id="ample"),
    ],
)
def test_modexp_0_0_0(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    execution_budget: int | None,
    success: bool,
) -> None:
    """Store the hash of the MODEXP output if the budget allows it."""
    sender = pre.fund_eoa()
    contract = pre.deploy_contract(code=CALLER_CODE)
    gas: int | Op = Op.GAS
    if execution_budget is not None:
        store = Op.SSTORE(key_warm=False, original_value=0, new_value=1)
        gas = execution_budget + store.gas_cost(fork) - store.gas_cost(Cancun)
    entry = pre.deploy_contract(
        code=Op.CALLDATACOPY(dest_offset=0, offset=0, size=Op.CALLDATASIZE)
        + Op.CALL(gas=gas, address=contract, args_size=Op.CALLDATASIZE)
    )

    tx = Transaction(
        sender=sender,
        to=entry,
        data=Bytes("30c8d1da")
        + Hash(0x20)
        + Hash(0x60)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0),
        state_gas_reservoir=0,
    )

    post = {contract: Account(storage={0: RESULT_HASH} if success else {})}

    state_test(pre=pre, post=post, tx=tx)
