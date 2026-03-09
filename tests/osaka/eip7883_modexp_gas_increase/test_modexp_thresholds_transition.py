"""
Test ModExp gas cost transition from EIP-7883 before & after the Osaka fork.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    EIPChecklist,
    Environment,
    Fork,
    Op,
    Transaction,
    TransitionFork,
    keccak256,
)

from ...byzantium.eip198_modexp_precompile.helpers import ModExpInput
from .spec import Spec, ref_spec_7883

REFERENCE_SPEC_GIT_PATH = ref_spec_7883.git_path
REFERENCE_SPEC_VERSION = ref_spec_7883.version

pytestmark = pytest.mark.valid_at_transition_to("Osaka")


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
    env: Environment,
    fork: TransitionFork,
    gas_old: int,
    gas_new: int,
    modexp_input: ModExpInput,
    modexp_expected: bytes,
) -> None:
    """
    Test ModExp gas cost transition from EIP-7883 before and after the Osaka
    hard fork.
    """

    def generate_code(fork: Fork) -> Bytecode:
        call_code = Op.CALL(
            address=Spec.MODEXP_ADDRESS,
            args_size=Op.CALLDATASIZE,
        )

        extra_gas = (
            Op.CALL(
                address=Spec.MODEXP_ADDRESS,
                args_size=Op.CALLDATASIZE,
                address_warm=True,
            ).gas_cost(fork.transitions_to())
            + Op.GAS.gas_cost(
                fork.transitions_to()
            )  # second GAS in measurement
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
        return code

    def calc_tx_gas_limit(fork: Fork) -> int:
        tx_gas_limit_cap = fork.transaction_gas_limit_cap() or env.gas_limit
        return tx_gas_limit_cap

    timestamps = [14_999, 15_000, 15_001]
    contracts = [
        pre.deploy_contract(generate_code(fork.fork_at(timestamp=t)))
        for t in timestamps
    ]
    gas_values = [gas_old, gas_new, gas_new]

    blocks = [
        Block(
            timestamp=ts,
            txs=[
                Transaction(
                    to=contract,
                    data=modexp_input,
                    sender=pre.fund_eoa(),
                    gas_limit=calc_tx_gas_limit(fork.fork_at(timestamp=ts)),
                )
            ],
        )
        for ts, contract in zip(timestamps, contracts, strict=False)
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
