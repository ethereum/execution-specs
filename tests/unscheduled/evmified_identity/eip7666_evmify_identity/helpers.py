"""Helpers for the EIP-7666 tests."""

from execution_testing import Address, Bytecode, Op

from .spec import Spec

IDENTITY = int.from_bytes(Spec.IDENTITY_PRECOMPILE_ADDRESS, "big")


def call_gas_used(address: Address | int) -> Bytecode:
    """Call `address` and leave the gas the call used on the stack."""
    return (
        Op.GAS
        + Op.POP(
            Op.CALL(
                gas=100_000,
                address=address,
                args_size=32,
                ret_offset=32,
                ret_size=32,
            )
        )
        + Op.GAS
        + Op.SWAP1
        + Op.SUB
    )


def compare_call_costs(twin: Address) -> Bytecode:
    """
    Call the identity address and `twin`, leaving 1 on the stack if both
    calls cost the same gas, else 0.
    """
    # Expand memory up front so neither call pays for it.
    return (
        Op.MSTORE(0, 0xC0FFEE)
        + Op.MSTORE(32, 0)
        + call_gas_used(IDENTITY)
        + call_gas_used(twin)
        + Op.EQ
    )
