"""
Test the EIP-3155 tracer's gas reads against every fork gas layout.

The tracer reads gas through structural protocols rather than fork
types, so each layout a fork uses is built here from the fork's own
gas meter: flat gas fields on the EVM (through Prague), state gas kept
on the meter (Amsterdam), and state gas kept in a reservoir component
or, for a frame transaction, on the frame context (Bogota).
"""

from types import SimpleNamespace
from typing import Any

import pytest
from ethereum.forks.amsterdam.fork_types import (
    ExecutionGas as AmsterdamExecutionGas,
)
from ethereum.forks.amsterdam.fork_types import StateGas as AmsterdamStateGas
from ethereum.forks.amsterdam.vm.gas import GasMeter as AmsterdamGasMeter
from ethereum.forks.bogota.fork_types import (
    ExecutionGas as BogotaExecutionGas,
)
from ethereum.forks.bogota.fork_types import StateGas as BogotaStateGas
from ethereum.forks.bogota.vm.gas import GasMeter as BogotaGasMeter
from ethereum.forks.bogota.vm.gas import (
    StateGasReservoir as BogotaStateGasReservoir,
)
from ethereum_types.numeric import Uint

from execution_testing.evm_tools.t8n.evm_trace.protocols import (
    evm_gas_left,
    evm_refund_counter,
    evm_state_gas_left,
)

GAS_LEFT = 5
STATE_GAS_LEFT = 7
REFUND_COUNTER = 3


def evm_with(**gas_fields: Any) -> SimpleNamespace:
    """Return a stand-in for a fork's `Evm` carrying the given gas fields."""
    return SimpleNamespace(
        pc=Uint(0),
        stack=[],
        memory=bytearray(),
        code=b"",
        running=True,
        **gas_fields,
    )


@pytest.mark.evm_tools
@pytest.mark.parametrize(
    "evm,state_gas_left",
    [
        pytest.param(
            evm_with(gas_left=Uint(GAS_LEFT), refund_counter=REFUND_COUNTER),
            None,
            id="flat_gas",
        ),
        pytest.param(
            evm_with(
                gas_meter=AmsterdamGasMeter(
                    gas_left=AmsterdamExecutionGas(Uint(GAS_LEFT)),
                    state_gas_left=AmsterdamStateGas(Uint(STATE_GAS_LEFT)),
                    state_gas_baseline=AmsterdamStateGas(Uint(STATE_GAS_LEFT)),
                    refund_counter=REFUND_COUNTER,
                ),
            ),
            Uint(STATE_GAS_LEFT),
            id="state_gas_on_meter",
        ),
        pytest.param(
            evm_with(
                gas_meter=BogotaGasMeter(
                    gas_left=BogotaExecutionGas(Uint(GAS_LEFT)),
                    reservoir=BogotaStateGasReservoir(
                        state_gas_left=BogotaStateGas(Uint(STATE_GAS_LEFT)),
                        state_gas_baseline=BogotaStateGas(
                            Uint(STATE_GAS_LEFT)
                        ),
                    ),
                    refund_counter=REFUND_COUNTER,
                ),
            ),
            Uint(STATE_GAS_LEFT),
            id="state_gas_in_reservoir",
        ),
        pytest.param(
            evm_with(
                gas_meter=BogotaGasMeter(
                    gas_left=BogotaExecutionGas(Uint(GAS_LEFT)),
                    reservoir=None,
                    refund_counter=REFUND_COUNTER,
                ),
                tx_env=SimpleNamespace(
                    frame_context=SimpleNamespace(
                        state_gas_left=BogotaStateGas(Uint(STATE_GAS_LEFT)),
                    ),
                ),
            ),
            Uint(STATE_GAS_LEFT),
            id="state_gas_on_frame_context",
        ),
    ],
)
def test_tracer_reads_every_gas_layout(
    evm: SimpleNamespace, state_gas_left: Uint | None
) -> None:
    """The tracer's gas reads resolve each fork's gas layout."""
    assert evm_gas_left(evm) == Uint(GAS_LEFT)
    assert evm_refund_counter(evm) == REFUND_COUNTER
    assert evm_state_gas_left(evm) == state_gas_left
