"""Shared helpers for the EIP-8038 state-access gas tests."""

from typing import List, Optional, Sequence, Union

from execution_testing import AccessList, Address, Bytecode, Fork


def opcode_overhead(
    measured: Bytecode, bare_opcode: Union[Bytecode, int], fork: Fork
) -> int:
    """
    Return the ``CodeGasMeasure`` overhead that strips the operand-PUSH
    wrapper from ``measured``, leaving only the measured opcode's own gas.

    ``measured`` is the runnable opcode plus its operand pushes;
    ``bare_opcode`` is the metadata-only opcode (a ``Bytecode``) or its
    already-computed bare gas (an ``int``). The overhead is their
    difference, so ``CodeGasMeasure`` subtracts the wrapper and the stored
    value equals the opcode's own runtime cost.
    """
    bare_gas = (
        bare_opcode
        if isinstance(bare_opcode, int)
        else bare_opcode.gas_cost(fork)
    )
    return measured.gas_cost(fork) - bare_gas


def warm_access_list(
    address: Address,
    warm: bool,
    *,
    storage_keys: Optional[Sequence[Union[int, bytes]]] = None,
) -> Optional[List[AccessList]]:
    """
    Return a one-entry access list warming ``address`` (optionally with
    ``storage_keys``) when ``warm`` is true, otherwise ``None``.
    """
    if not warm:
        return None
    return [AccessList(address=address, storage_keys=list(storage_keys or []))]
