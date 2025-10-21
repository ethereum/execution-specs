"""
Test ModExp gas cost transition from EIP-7883 before & after the Osaka fork.
"""

import pytest
from ethereum_test_checklists import EIPChecklist
from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Transaction,
    keccak256,
)
from ethereum_test_vm import Opcodes as Op

from ...byzantium.eip198_modexp_precompile.helpers import ModExpInput
from .spec import Spec, ref_spec_7883

REFERENCE_SPEC_GIT_PATH = ref_spec_7883.git_path
REFERENCE_SPEC_VERSION = ref_spec_7883.version

pytestmark = pytest.mark.valid_at_transition_to("Osaka", subsequent_forks=True)


@pytest.mark.parametrize(
    "modexp_input,modexp_expected,gas_old,gas_new",
    [
        pytest.param(Spec.modexp_input, Spec.modexp_expected, 200, 1200),
    ],
    ids=[""],
)
@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
@EIPChecklist.Precompile.Test.ForkTransition.After.Warm()
@EIPChecklist.GasCostChanges.Test.ForkTransition.Before()
@EIPChecklist.GasCostChanges.Test.ForkTransition.After()
def test_modexp_fork_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_old: int,
    gas_new: int,
    tx_gas_limit: int,
    modexp_input: ModExpInput,
    modexp_expected: bytes,
) -> None:
    """
    Test ModExp gas cost transition from EIP-7883 before and after the Osaka
    hard fork.
    """
    call_code = Op.CALL(
        address=Spec.MODEXP_ADDRESS,
        args_size=Op.CALLDATASIZE,
    )

    gas_costs = fork.gas_costs()
    extra_gas = (
        gas_costs.G_WARM_ACCOUNT_ACCESS
        + (gas_costs.G_VERY_LOW * (len(Op.CALL.kwargs) - 2))
        + (gas_costs.G_BASE * 3)
    )
    code = (
        Op.CALLDATACOPY(dest_offset=0, offset=0, size=Op.CALLDATASIZE)
        + Op.GAS  # [gas_start]
        + call_code  # [gas_start, call_result]
        + Op.GAS  # [gas_start, call_result, gas_end]
        + Op.SWAP1  # [gas_start, gas_end, call_result]
        + Op.POP  # [gas_start, gas_end]
        + Op.PUSH2[extra_gas]  # [gas_start, gas_end, extra_gas]
        + Op.ADD  # [gas_start, gas_end + extra_gas]
        + Op.SWAP1  # [gas_end + extra_gas, gas_start]
        + Op.SUB  # [gas_start - (gas_end + extra_gas)]
        + Op.TIMESTAMP  # [gas_start - (gas_end + extra_gas), TIMESTAMP]
        + Op.SSTORE  # []
    )

    # Verification the precompile call result
    code += Op.RETURNDATACOPY(
        dest_offset=0, offset=0, size=Op.RETURNDATASIZE()
    ) + Op.SSTORE(
        Op.AND(Op.TIMESTAMP, 0xFF),
        Op.SHA3(0, Op.RETURNDATASIZE()),
    )

    senders = [pre.fund_eoa() for _ in range(3)]
    contracts = [pre.deploy_contract(code) for _ in range(3)]
    timestamps = [14_999, 15_000, 15_001]
    gas_values = [gas_old, gas_new, gas_new]

    blocks = [
        Block(
            timestamp=ts,
            txs=[
                Transaction(
                    to=contract,
                    data=modexp_input,
                    sender=sender,
                    gas_limit=tx_gas_limit,
                )
            ],
        )
        for ts, contract, sender in zip(
            timestamps, contracts, senders, strict=False
        )
    ]

    post = {
        contract: Account(
            storage={ts: gas, ts & 0xFF: keccak256(bytes(modexp_expected))}
        )
        for contract, ts, gas in zip(
            contracts, timestamps, gas_values, strict=False
        )
    }

    blockchain_test(
        pre=pre,
        blocks=blocks,
        post=post,
    )
