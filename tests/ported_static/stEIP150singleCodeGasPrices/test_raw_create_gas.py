"""
Test the gas of a contract creation with empty init code.

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawCreateGasFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCreateGasMemoryFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCreateGasValueTransferFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCreateGasValueTransferMemoryFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCreateFailGasValueTransferFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCreateFailGasValueTransfer2Filler.json

@manually-enhanced: Do not overwrite. The six fillers differed only in
the endowment, whether the creator could afford it, and the size of
the init code. `creator` measures one CREATE or CREATE2 in
`CodeGasMeasure` and stores the gas in slot 0. The init code is the
creator's zeroed memory, so it is empty or 8000 bytes of STOP, and the
created account gets the endowment and no code. A creator one wei short
of the endowment fails the creation before it starts: nothing is
created, its nonce stays put, and only the execution gas is charged,
never the state gas of a new account. The expected value comes from the
framework gas calculation, with the memory and init code sizes as
metadata.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op, Opcodes

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

GAS_SLOT = 0
ENDOWMENT = 0xA
MEMORY_SIZE = 0x1F40

pytestmark = [
    pytest.mark.ported_from(
        [
            "state_tests/stEIP150singleCodeGasPrices/RawCreateGasFiller.json",
            "state_tests/stEIP150singleCodeGasPrices/RawCreateGasMemoryFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCreateGasValueTransferFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCreateGasValueTransferMemoryFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCreateFailGasValueTransferFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawCreateFailGasValueTransfer2Filler.json",  # noqa: E501
        ],
    ),
    pytest.mark.valid_from("Frontier"),
    pytest.mark.with_all_create_opcodes(),
]


@pytest.mark.parametrize(
    "endowment",
    ["no_value", "value", "value_above_balance"],
)
@pytest.mark.parametrize(
    "init_code_size", [0, MEMORY_SIZE], ids=["empty", "memory"]
)
def test_raw_create_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Opcodes,
    endowment: str,
    init_code_size: int,
) -> None:
    """Store the gas of one CREATE or CREATE2 of zeroed init code."""
    value: int
    if endowment == "no_value":
        value, balance = 0, 0
    elif endowment == "value":
        value, balance = ENDOWMENT, ENDOWMENT
    elif endowment == "value_above_balance":
        value, balance = ENDOWMENT, ENDOWMENT - 1
    else:
        raise ValueError(f"Unknown endowment: {endowment}")
    fails = value > balance

    create: Bytecode
    if create_opcode == Op.CREATE:
        create = Op.CREATE(
            value=value,
            offset=0,
            size=init_code_size,
            new_memory_size=init_code_size,
            init_code_size=init_code_size,
        )
    elif create_opcode == Op.CREATE2:
        create = Op.CREATE2(
            value=value,
            offset=0,
            size=init_code_size,
            salt=0,
            new_memory_size=init_code_size,
            init_code_size=init_code_size,
        )
    else:
        raise ValueError(f"Unknown create opcode: {create_opcode}")

    creator = pre.deploy_contract(
        code=CodeGasMeasure(
            code=create,
            extra_stack_items=1,
            sstore_key=GAS_SLOT,
        )
        + Op.STOP,
        balance=balance,
    )

    # The new account's state gas must come out of the measured frame,
    # not out of a reservoir (EIP-8037). The failing creation is held to
    # the same rule, so a state charge there would be measured too.
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=creator,
        protected=fork.supports_protected_txs(),
        state_gas_reservoir=0,
    )

    created = compute_create_address(
        address=creator,
        nonce=1,
        salt=0,
        initcode=bytes(init_code_size),
        opcode=create_opcode,
    )
    post: dict
    if fails:
        # A creation that cannot pay its endowment charges no state gas.
        post = {
            creator: Account(
                nonce=1, storage={GAS_SLOT: create.execution_cost(fork)}
            ),
            created: Account.NONEXISTENT,
        }
    else:
        post = {
            creator: Account(
                nonce=2, storage={GAS_SLOT: create.gas_cost(fork)}
            ),
            created: Account(
                nonce=int(fork.is_eip_enabled(161)), balance=value, code=b""
            ),
        }

    state_test(pre=pre, post=post, tx=tx)
