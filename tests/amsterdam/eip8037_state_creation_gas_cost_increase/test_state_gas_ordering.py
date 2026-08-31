"""
Test state gas consumption ordering under EIP-8037.

When an opcode charges both execution gas and state gas, execution gas MUST
be charged first. If execution gas OOGs, state gas is not consumed. This
prevents the parent's reservoir from being inflated on frame failure.

Each test gives a child frame exactly 1 gas less than needed, then uses
a probe contract to detect whether the parent's reservoir was inflated
by incorrectly consumed state gas.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Header,
    Op,
    Transaction,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version

WORD_SIZE = 32


@pytest.mark.parametrize(
    "oog_step",
    [
        pytest.param("create_base", id="oog_on_create_base"),
        pytest.param("init_code_word_cost", id="oog_on_init_code_word_cost"),
    ],
)
@pytest.mark.with_all_create_opcodes()
@pytest.mark.valid_from("EIP8037")
def test_create_oog_full_burn_no_state_credit(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    oog_step: str,
) -> None:
    """
    Verify a CREATE OOG inside a non-creation tx burns the whole
    tx gas_limit — no state-gas leftover is credited at tx-end.
    """
    if oog_step == "create_base":
        initcode_size = 0
    else:
        initcode_size = WORD_SIZE

    if create_opcode == Op.CREATE:
        create_op = create_opcode(
            value=0, offset=0, size=initcode_size, init_code_size=initcode_size
        )
    else:
        create_op = create_opcode(
            value=0,
            offset=0,
            size=initcode_size,
            salt=0,
            init_code_size=initcode_size,
        )

    if oog_step == "create_base":
        factory_code = create_op
    else:
        factory_code = Op.MSTORE(0, 0, new_memory_size=WORD_SIZE) + create_op
    factory = pre.deploy_contract(factory_code)

    # One gas short of the CREATE's full cost (execution plus the NEW_ACCOUNT
    # state charge), so it OOGs on the account-creation charge.
    body_gas = factory_code.gas_cost(fork) - 1

    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()
    tx_gas_limit = intrinsic_calc() + body_gas

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=factory,
        gas_limit=tx_gas_limit,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=tx_gas_limit),
            ),
        ],
        post={},
    )
