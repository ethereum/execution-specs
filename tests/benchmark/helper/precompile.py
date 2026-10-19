"""Precompile benchmark targets and input-size tuning."""

import math

from execution_testing import Fork, Op, OpcodeTarget


class Precompile:
    """Target opcode labels for precompile benchmarks."""

    ECRECOVER = OpcodeTarget("ECRECOVER", Op.STATICCALL)
    SHA256 = OpcodeTarget("SHA2-256", Op.STATICCALL)
    RIPEMD160 = OpcodeTarget("RIPEMD-160", Op.STATICCALL)
    IDENTITY = OpcodeTarget("IDENTITY", Op.STATICCALL)
    MODEXP = OpcodeTarget("MODEXP", Op.STATICCALL)
    BN128_ADD = OpcodeTarget("BN128_ADD", Op.STATICCALL)
    BN128_MUL = OpcodeTarget("BN128_MUL", Op.STATICCALL)
    BN128_PAIRING = OpcodeTarget("BN128_PAIRING", Op.STATICCALL)
    BLAKE2F = OpcodeTarget("BLAKE2F", Op.STATICCALL)
    POINT_EVALUATION = OpcodeTarget("POINT_EVALUATION", Op.STATICCALL)
    P256VERIFY = OpcodeTarget("P256VERIFY", Op.STATICCALL)
    BLS12_G1ADD = OpcodeTarget("BLS12_G1ADD", Op.STATICCALL)
    BLS12_G1MSM = OpcodeTarget("BLS12_G1MSM", Op.STATICCALL)
    BLS12_G2ADD = OpcodeTarget("BLS12_G2ADD", Op.STATICCALL)
    BLS12_G2MSM = OpcodeTarget("BLS12_G2MSM", Op.STATICCALL)
    BLS12_PAIRING = OpcodeTarget("BLS12_PAIRING", Op.STATICCALL)
    BLS12_MAP_FP_TO_G1 = OpcodeTarget("BLS12_MAP_FP_TO_G1", Op.STATICCALL)
    BLS12_MAP_FP2_TO_G2 = OpcodeTarget("BLS12_MAP_FP2_TO_G2", Op.STATICCALL)


def calculate_optimal_input_length(
    available_gas: int,
    fork: Fork,
    static_cost: int,
    per_word_dynamic_cost: int,
    bytes_per_unit_of_work: int,
) -> int:
    """
    Calculate the optimal input length to maximize precompile work.

    This function finds the input size that maximizes the total amount of
    work (in terms of bytes processed) a precompile can perform given a
    fixed gas budget. It balances the trade-off between making more calls
    with smaller inputs versus fewer calls with larger inputs.

    Args:
        available_gas: Total gas available for precompile calls.
        fork: The fork to use for gas cost calculations.
        static_cost: Static gas cost per precompile call.
        per_word_dynamic_cost: Dynamic gas cost per 32-byte word of input.
        bytes_per_unit_of_work: Number of bytes processed per unit of work.

    Returns:
        The optimal input length in bytes that maximizes total work.

    """
    mem_exp_gas_calculator = fork.memory_expansion_gas_calculator()

    precompile_call = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS,
            address=0x01,  # Placeholder Address
            args_offset=Op.PUSH0,
            args_size=Op.PUSH0,
            ret_offset=Op.PUSH0,
            ret_size=Op.PUSH0,
            # gas cost
            address_warm=True,
        )
    )
    basic_gas = precompile_call.gas_cost(fork)

    max_work = 0
    optimal_input_length = 0

    for input_length in range(1, 1_000_000, 32):
        iteration_gas_cost = (
            basic_gas
            + static_cost  # Precompile static cost
            + math.ceil(input_length / 32) * per_word_dynamic_cost
            # Precompile dynamic cost
        )

        # From the available gas, subtract the memory expansion costs
        # considering the current input size length.
        available_gas_after_expansion = max(
            0, available_gas - mem_exp_gas_calculator(new_bytes=input_length)
        )

        # Calculate how many calls we can do.
        num_calls = available_gas_after_expansion // iteration_gas_cost
        total_work = num_calls * math.ceil(
            input_length / bytes_per_unit_of_work
        )

        # If we found an input size with better total work, save it.
        if total_work > max_work:
            max_work = total_work
            optimal_input_length = input_length

    return optimal_input_length
