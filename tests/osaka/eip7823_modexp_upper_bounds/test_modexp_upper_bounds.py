"""
Test [EIP-7823: Set upper bounds for MODEXP](https://eips.ethereum.org/EIPS/eip-7823).
"""

from typing import Dict

import pytest
from ethereum_test_checklists import EIPChecklist
from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    StateTestFiller,
    Transaction,
    keccak256,
)
from ethereum_test_vm import Opcodes as Op

from ...byzantium.eip198_modexp_precompile.helpers import ModExpInput
from ..eip7883_modexp_gas_increase.spec import Spec
from .spec import ref_spec_7823

REFERENCE_SPEC_GIT_PATH = ref_spec_7823.git_path
REFERENCE_SPEC_VERSION = ref_spec_7823.version


@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize(
    "modexp_input,modexp_expected,call_succeeds",
    [
        pytest.param(
            ModExpInput(
                base=b"\0" * (Spec.MAX_LENGTH_BYTES + 1),
                exponent=b"\0",
                modulus=b"\2",
            ),
            Spec.modexp_error,
            False,
            id="excess_length_base",
        ),
        pytest.param(
            ModExpInput(
                base=b"\0",
                exponent=b"\0" * (Spec.MAX_LENGTH_BYTES + 1),
                modulus=b"\2",
            ),
            Spec.modexp_error,
            False,
            id="excess_length_exponent",
        ),
        pytest.param(
            ModExpInput(
                base=b"\0",
                exponent=b"\0",
                modulus=b"\0" * (Spec.MAX_LENGTH_BYTES) + b"\2",
            ),
            Spec.modexp_error,
            False,
            id="excess_length_modulus",
        ),
        pytest.param(
            ModExpInput(
                base=b"",
                exponent=b"\0" * (Spec.MAX_LENGTH_BYTES + 1),
                modulus=b"",
            ),
            Spec.modexp_error,
            False,
            id="exp_1025_base_0_mod_0",
        ),
        pytest.param(
            ModExpInput(
                base=b"",
                # Non-zero exponent is cancelled with zero multiplication
                # complexity pre EIP-7823.
                exponent=b"\xff" * (Spec.MAX_LENGTH_BYTES + 1),
                modulus=b"",
            ),
            Spec.modexp_error,
            False,
            id="expFF_1025_base_0_mod_0",
        ),
        pytest.param(
            ModExpInput(
                base=b"\0" * Spec.MAX_LENGTH_BYTES,
                exponent=b"\xff" * (Spec.MAX_LENGTH_BYTES + 1),
                modulus=b"",
            ),
            Spec.modexp_error,
            False,
            id="expFF_1025_base_1024_mod_0",
        ),
        pytest.param(
            ModExpInput(
                base=b"\0" * (Spec.MAX_LENGTH_BYTES + 1),
                exponent=b"\xff" * (Spec.MAX_LENGTH_BYTES + 1),
                modulus=b"",
            ),
            Spec.modexp_error,
            False,
            id="expFF_1025_base_1025_mod_0",
        ),
        pytest.param(
            ModExpInput(
                base=b"\0" * (Spec.MAX_LENGTH_BYTES + 1),
                exponent=b"",
                modulus=b"",
            ),
            Spec.modexp_error,
            False,
            id="exp_0_base_1025_mod_0",
        ),
        pytest.param(
            ModExpInput(
                base=b"\0" * (Spec.MAX_LENGTH_BYTES + 1),
                exponent=b"",
                modulus=b"\2",
            ),
            Spec.modexp_error,
            False,
            id="exp_0_base_1025_mod_1",
        ),
        pytest.param(
            ModExpInput(
                base=b"",
                exponent=b"",
                modulus=b"\0" * (Spec.MAX_LENGTH_BYTES + 1),
            ),
            Spec.modexp_error,
            False,
            id="exp_0_base_0_mod_1025",
        ),
        pytest.param(
            ModExpInput(
                base=b"\1",
                exponent=b"",
                modulus=b"\0" * (Spec.MAX_LENGTH_BYTES + 1),
            ),
            Spec.modexp_error,
            False,
            id="exp_0_base_1_mod_1025",
        ),
        pytest.param(
            ModExpInput(
                base=b"",
                exponent=Bytes("80"),
                modulus=b"",
                declared_exponent_length=2**64,
            ),
            Spec.modexp_error,
            False,
            id="exp_2_pow_64_base_0_mod_0",
        ),
        # Implementation coverage tests
        pytest.param(
            ModExpInput(
                base=b"\xff" * (Spec.MAX_LENGTH_BYTES + 1),
                exponent=b"\xff" * (Spec.MAX_LENGTH_BYTES + 1),
                modulus=b"\xff" * (Spec.MAX_LENGTH_BYTES + 1),
            ),
            Spec.modexp_error,
            False,
            id="all_exceed_check_ordering",
        ),
        pytest.param(
            ModExpInput(
                base=b"\x00" * Spec.MAX_LENGTH_BYTES,
                exponent=b"\xff" * (Spec.MAX_LENGTH_BYTES + 1),
                modulus=b"\xff" * (Spec.MAX_LENGTH_BYTES + 1),
            ),
            Spec.modexp_error,
            False,
            id="exp_mod_exceed_base_ok",
        ),
        pytest.param(
            ModExpInput(
                # Bitwise pattern for Nethermind optimization
                base=b"\xaa" * (Spec.MAX_LENGTH_BYTES + 1),
                exponent=b"\x55" * Spec.MAX_LENGTH_BYTES,
                modulus=b"\xff" * Spec.MAX_LENGTH_BYTES,
            ),
            Spec.modexp_error,
            False,
            id="bitwise_pattern_base_exceed",
        ),
        pytest.param(
            ModExpInput(
                base=b"",
                exponent=b"",
                modulus=b"",
                # Near max uint64 for revm conversion test
                declared_base_length=2**63 - 1,
                declared_exponent_length=1,
                declared_modulus_length=1,
            ),
            Spec.modexp_error,
            False,
            id="near_uint64_max_base",
        ),
        pytest.param(
            ModExpInput(
                base=b"\x01" * Spec.MAX_LENGTH_BYTES,
                exponent=b"",
                modulus=b"\x02" * (Spec.MAX_LENGTH_BYTES + 1),
                declared_exponent_length=0,
            ),
            Spec.modexp_error,
            False,
            id="zero_exp_mod_exceed",
        ),
        pytest.param(
            ModExpInput(
                base=b"\x01" * Spec.MAX_LENGTH_BYTES,
                exponent=b"\x00",
                modulus=b"\x02",
            ),
            b"\x01",
            True,
            id="base_boundary",
        ),
        pytest.param(
            ModExpInput(
                base=b"\x01",
                exponent=b"\x00" * Spec.MAX_LENGTH_BYTES,
                modulus=b"\x02",
            ),
            b"\x01",
            True,
            id="exp_boundary",
        ),
        pytest.param(
            ModExpInput(
                base=b"\x01",
                exponent=b"\x00",
                modulus=b"\x02" * Spec.MAX_LENGTH_BYTES,
            ),
            b"\x01".rjust(Spec.MAX_LENGTH_BYTES, b"\x00"),
            True,
            id="mod_boundary",
        ),
        pytest.param(
            ModExpInput(
                base=b"\x01" * Spec.MAX_LENGTH_BYTES,
                exponent=b"\x00",
                modulus=b"\x02" * Spec.MAX_LENGTH_BYTES,
            ),
            b"\x01".rjust(Spec.MAX_LENGTH_BYTES, b"\x00"),
            True,
            id="base_mod_boundary",
        ),
    ],
)
@EIPChecklist.Precompile.Test.Inputs.MaxValues
@EIPChecklist.Precompile.Test.OutOfBounds.Max
def test_modexp_upper_bounds(
    state_test: StateTestFiller,
    modexp_input: ModExpInput,
    modexp_expected: bytes,
    precompile_gas: int,
    fork: Fork,
    tx: Transaction,
    post: Dict,
    pre: Alloc,
) -> None:
    """Test the MODEXP precompile input bounds."""
    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "modexp_input,modexp_expected",
    [
        pytest.param(
            ModExpInput(
                base=b"\1" * (Spec.MAX_LENGTH_BYTES + 1),
                exponent=b"\0",
                modulus=b"\2",
            ),
            b"\1",
            id="base_1_exp_0_mod_2",
        ),
    ],
)
@pytest.mark.valid_at_transition_to("Osaka", subsequent_forks=True)
def test_modexp_upper_bounds_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    precompile_gas: int,
    modexp_input: ModExpInput,
    modexp_expected: bytes,
) -> None:
    """
    Test MODEXP upper bounds enforcement transition from before to after Osaka
    hard fork.
    """
    call_code = Op.CALL(
        address=Spec.MODEXP_ADDRESS,
        args_size=Op.CALLDATASIZE,
    )

    code = (
        Op.CALLDATACOPY(size=Op.CALLDATASIZE)
        + Op.SSTORE(
            Op.TIMESTAMP,
            call_code,
        )
        + Op.RETURNDATACOPY(size=Op.RETURNDATASIZE())
        + Op.SSTORE(
            Op.AND(Op.TIMESTAMP, 0xFF),
            Op.SHA3(0, Op.RETURNDATASIZE()),
        )
    )

    senders = [pre.fund_eoa() for _ in range(3)]
    contracts = [pre.deploy_contract(code) for _ in range(3)]
    timestamps = [14_999, 15_000, 15_001]  # Before, at, and after transition
    expected_results = [True, False, False]

    blocks = [
        Block(
            timestamp=ts,
            txs=[
                Transaction(
                    to=contract,
                    data=bytes(modexp_input),
                    sender=sender,
                    gas_limit=6_000_000,
                )
            ],
        )
        for ts, contract, sender in zip(
            timestamps, contracts, senders, strict=False
        )
    ]

    post = {
        contract: Account(
            storage={
                ts: expected,
                ts & 0xFF: keccak256(modexp_expected)
                if expected
                else keccak256(Spec.modexp_error),
            }
        )
        for contract, ts, expected in zip(
            contracts, timestamps, expected_results, strict=False
        )
    }

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )
