"""
Test_static_raw_call_gas_ask.

Ported from:
state_tests/stStaticCall/static_RawCallGasAskFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_RawCallGasAskFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "mem_expansion",
    [
        pytest.param(False, id="without_mem_expansion"),
        pytest.param(True, id="with_mem_expansion"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_raw_call_gas_ask(
    state_test: StateTestFiller,
    pre: Alloc,
    mem_expansion: bool,
    fork: Fork,
) -> None:
    """Test_static_raw_call_gas_ask."""
    sender = pre.fund_eoa()

    subcall_code = Op.MSTORE(0, Op.GAS, new_memory_size=32) + Op.STOP
    subcall_contract = pre.deploy_contract(code=subcall_code)

    mem_expansion_size = 0x1F40
    static_call_code = (
        Op.STATICCALL(
            address=subcall_contract,
            args_size=mem_expansion_size,
            ret_size=mem_expansion_size,
            new_memory_size=mem_expansion_size,
        )
        if mem_expansion
        else Op.STATICCALL(
            address=subcall_contract,
        )
    )
    static_call_contract = pre.deploy_contract(
        code=CodeGasMeasure(
            code=static_call_code,
            extra_stack_items=1,
            sstore_key=1,
        ),
    )

    gas_cost = static_call_code.gas_cost(fork) + subcall_code.gas_cost(fork)
    post = {static_call_contract: Account(storage={1: gas_cost})}
    tx = Transaction(sender=sender, to=static_call_contract)

    state_test(pre=pre, post=post, tx=tx)
