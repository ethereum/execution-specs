"""Fixtures for the EIP-7954 max contract size tests."""

import pytest
from execution_testing import Address, Alloc, Bytecode, Fork, Op


@pytest.fixture
def max_code_size_contract(
    pre: Alloc,
    fork: Fork,
) -> tuple[Address, Bytecode]:
    """
    Deploy a max-size self-checking contract deterministically.

    The contract uses its own ADDRESS to query EXTCODESIZE, EXTCODEHASH,
    and EXTCODECOPY on itself, storing results in storage slots 0-2.
    Padded with JUMPDESTs to reach the fork's max code size.
    """
    code_size = fork.max_code_size()
    logic = (
        Op.SSTORE(0, Op.EXTCODESIZE(Op.ADDRESS, address_warm=True))
        + Op.SSTORE(1, Op.EXTCODEHASH(Op.ADDRESS, address_warm=True))
        + Op.EXTCODECOPY(
            Op.ADDRESS,
            0,
            0,
            Op.EXTCODESIZE(Op.ADDRESS, address_warm=True),
            # gas accounting
            address_warm=True,
            data_size=code_size,
            new_memory_size=code_size,
        )
        + Op.SSTORE(
            2,
            Op.SHA3(
                0,
                Op.EXTCODESIZE(Op.ADDRESS, address_warm=True),
                # gas accounting
                data_size=code_size,
                new_memory_size=code_size,
            ),
        )
        + Op.STOP
    )
    target_code = logic + Op.JUMPDEST * (fork.max_code_size() - len(logic))
    target = pre.deterministic_deploy_contract(deploy_code=target_code)
    return target, target_code
