from typing import Optional, cast

from ethereum_types.numeric import Uint

import ethereum.trace


def test_modify_evm_trace() -> None:
    trace1: Optional[ethereum.trace.TraceEvent] = None
    trace2: Optional[ethereum.trace.TraceEvent] = None

    def tracer1(
        evm: object,  # noqa: U100
        event: ethereum.trace.TraceEvent,
        trace_memory: bool = False,  # noqa: U100
        trace_stack: bool = True,  # noqa: U100
        trace_return_data: bool = False,  # noqa: U100
    ) -> None:
        nonlocal trace1
        trace1 = event

    def tracer2(
        evm: object,  # noqa: U100
        event: ethereum.trace.TraceEvent,
        trace_memory: bool = False,  # noqa: U100
        trace_stack: bool = True,  # noqa: U100
        trace_return_data: bool = False,  # noqa: U100
    ) -> None:
        nonlocal trace2
        trace2 = event

    ethereum.trace.set_evm_trace(tracer1)

    from ethereum.prague.vm import Evm, Message
    from ethereum.prague.vm.gas import charge_gas

    evm = Evm(
        pc=Uint(1),
        stack=[],
        memory=bytearray(),
        code=b"",
        gas_left=Uint(100),
        valid_jump_destinations=set(),
        logs=(),
        refund_counter=0,
        running=True,
        message=cast(Message, object()),
        output=b"",
        accounts_to_delete=set(),
        return_data=b"",
        error=None,
        accessed_addresses=set(),
        accessed_storage_keys=set(),
    )

    charge_gas(evm, Uint(5))

    assert trace2 is None
    assert isinstance(trace1, ethereum.trace.GasAndRefund)
    assert trace1.gas_cost == 5

    ethereum.trace.set_evm_trace(tracer2)

    charge_gas(evm, Uint(6))

    # Check that the old event is unmodified.
    assert isinstance(trace1, ethereum.trace.GasAndRefund)
    assert trace1.gas_cost == 5

    # Check that the new event is populated.
    assert isinstance(trace2, ethereum.trace.GasAndRefund)
    assert trace2.gas_cost == 6
