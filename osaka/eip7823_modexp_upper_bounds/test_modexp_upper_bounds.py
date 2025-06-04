"""
abstract: Test [EIP-7823: Set upper bounds for MODEXP](https://eips.ethereum.org/EIPS/eip-7823)
    Tests upper bounds of the MODEXP precompile.
"""

import pytest

from ethereum_test_forks import Fork, Osaka
from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.vm.opcode import Opcodes as Op

from ...byzantium.eip198_modexp_precompile.helpers import ModExpInput, ModExpOutput
from ..eip7883_modexp_gas_increase.spec import Spec, Spec7883

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7823.md"
REFERENCE_SPEC_VERSION = "c8321494fdfbfda52ad46c3515a7ca5dc86b857c"

MAX_LENGTH_BYTES = 1024


@pytest.fixture
def precompile_gas(fork: Fork, mod_exp_input: ModExpInput) -> int:
    """Calculate gas cost for the ModExp precompile and verify it matches expected gas."""
    spec = Spec if fork < Osaka else Spec7883
    calculated_gas = spec.calculate_gas_cost(
        len(mod_exp_input.base),
        len(mod_exp_input.modulus),
        len(mod_exp_input.exponent),
        mod_exp_input.exponent,
    )
    return calculated_gas


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "mod_exp_input",
    [
        pytest.param(
            ModExpInput(
                base=b"\0" * (MAX_LENGTH_BYTES + 1),
                exponent=b"\0",
                modulus=b"\2",
            ),
            id="excess_length_base",
        ),
        pytest.param(
            ModExpInput(
                base=b"\0",
                exponent=b"\0" * (MAX_LENGTH_BYTES + 1),
                modulus=b"\2",
            ),
            id="excess_length_exponent",
        ),
        pytest.param(
            ModExpInput(
                base=b"\0",
                exponent=b"\0",
                modulus=b"\0" * (MAX_LENGTH_BYTES) + b"\2",
            ),
            id="excess_length_modulus",
        ),
    ],
)
def test_modexp_upper_bounds(
    state_test: StateTestFiller,
    mod_exp_input: ModExpInput,
    precompile_gas: int,
    fork: Fork,
    pre: Alloc,
):
    """Test the MODEXP precompile."""
    sender = pre.fund_eoa()

    account = pre.deploy_contract(
        # Store all CALLDATA into memory (offset 0)
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
        # Store the returned CALL status (success = 1, fail = 0) into slot 0:
        + Op.SSTORE(
            0,
            # Setup stack to CALL into ModExp with the CALLDATA and CALL into it (+ pop value)
            Op.CALL(
                gas=precompile_gas,
                address=0x05,
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE(),
            ),
        )
        # STOP (handy for tracing)
        + Op.STOP(),
    )

    intrinsic_gas_cost_calc = fork.transaction_intrinsic_cost_calculator()
    intrinsic_gas_cost = intrinsic_gas_cost_calc(calldata=mod_exp_input)
    memory_expansion_gas_calc = fork.memory_expansion_gas_calculator()
    memory_expansion_gas = memory_expansion_gas_calc(new_bytes=len(bytes(mod_exp_input)))

    gas_limit = intrinsic_gas_cost + (precompile_gas * 64 // 63) + memory_expansion_gas + 100_000
    env = Environment(gas_limit=gas_limit)

    tx = Transaction(
        ty=0x0,
        to=account,
        data=mod_exp_input,
        gas_limit=gas_limit,
        protected=True,
        sender=sender,
    )
    if (
        len(mod_exp_input.base) <= MAX_LENGTH_BYTES
        and len(mod_exp_input.exponent) <= MAX_LENGTH_BYTES
        and len(mod_exp_input.modulus) <= MAX_LENGTH_BYTES
    ) or fork < Osaka:
        output = ModExpOutput(call_success=True, returned_data="0x01")
    else:
        output = ModExpOutput(call_success=False, returned_data="0x")

    post = {account: Account(storage={0: output.call_success})}

    state_test(env=env, pre=pre, post=post, tx=tx)
