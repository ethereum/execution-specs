"""
Test the gas of reading another account's balance or code.

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawBalanceGasFiller.json
state_tests/stEIP150singleCodeGasPrices/RawExtCodeSizeGasFiller.json
state_tests/stEIP150singleCodeGasPrices/RawExtCodeCopyGasFiller.json
state_tests/stEIP150singleCodeGasPrices/RawExtCodeCopyMemoryGasFiller.json

@manually-enhanced: Do not overwrite. The four fillers differed only in
the measured opcode, so one test measures BALANCE, EXTCODESIZE or
EXTCODECOPY (with a small or a memory-expanding copy) in `gas_meter`,
storing the gas in slot 0. Each opcode reads either the sender, which
is warm from the start of the transaction, or `code_holder`, which is
cold. The expected value comes from the framework gas calculation, with
the warmth, copy size and memory size as metadata.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op, Opcode

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

GAS_SLOT = 0
COPY_DEST_OFFSET = 0x20
# Code that is only read, never executed.
HELD_CODE = bytes.fromhex(
    "0112233445566778899101112131415161718191202122232425"
)

pytestmark = [
    pytest.mark.ported_from(
        [
            "state_tests/stEIP150singleCodeGasPrices/RawBalanceGasFiller.json",
            "state_tests/stEIP150singleCodeGasPrices/RawExtCodeSizeGasFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawExtCodeCopyGasFiller.json",  # noqa: E501
            "state_tests/stEIP150singleCodeGasPrices/RawExtCodeCopyMemoryGasFiller.json",  # noqa: E501
        ],
    ),
    pytest.mark.valid_from("Frontier"),
]


@pytest.mark.parametrize(
    "opcode, copy_size",
    [
        pytest.param(Op.BALANCE, None, id="balance"),
        pytest.param(Op.EXTCODESIZE, None, id="extcodesize"),
        pytest.param(Op.EXTCODECOPY, 0x14, id="extcodecopy"),
        pytest.param(Op.EXTCODECOPY, 0x2B70, id="extcodecopy_memory"),
    ],
)
@pytest.mark.parametrize("accessed", ["sender", "code_holder"])
def test_raw_account_access_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Opcode,
    copy_size: int | None,
    accessed: str,
) -> None:
    """Store the gas of one BALANCE, EXTCODESIZE or EXTCODECOPY."""
    sender = pre.fund_eoa()
    code_holder = pre.deploy_contract(code=HELD_CODE)

    address: Address
    if accessed == "sender":
        # The transaction sender is warm from the start (EIP-2929).
        address, address_warm = sender, True
    elif accessed == "code_holder":
        address, address_warm = code_holder, False
    else:
        raise ValueError(f"Unknown accessed account: {accessed}")

    measured: Bytecode
    if opcode == Op.EXTCODECOPY:
        assert copy_size is not None
        measured = Op.EXTCODECOPY(
            address=address,
            dest_offset=COPY_DEST_OFFSET,
            offset=0,
            size=copy_size,
            address_warm=address_warm,
            data_size=copy_size,
            new_memory_size=COPY_DEST_OFFSET + copy_size,
        )
    elif opcode in (Op.BALANCE, Op.EXTCODESIZE):
        measured = opcode(address=address, address_warm=address_warm)
    else:
        raise ValueError(f"Unknown opcode: {opcode}")

    gas_meter = pre.deploy_contract(
        code=CodeGasMeasure(
            code=measured,
            extra_stack_items=measured.pushed_stack_items
            - measured.popped_stack_items,
            sstore_key=GAS_SLOT,
        )
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=gas_meter,
        protected=fork.supports_protected_txs(),
    )

    post = {gas_meter: Account(storage={GAS_SLOT: measured.gas_cost(fork)})}

    state_test(pre=pre, post=post, tx=tx)
