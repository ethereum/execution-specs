"""
Contracts the protocol calls while processing a block.

Before a block's transactions run, the protocol calls the beacon roots and
block history contracts from [`SYSTEM_ADDRESS`] to record the parent beacon
block root and the parent block hash. After them, it calls the request
contracts to collect the requests queued during the block. Block processing
depends on the code of these [`SYSTEM_CONTRACTS`], so their code cannot be
replaced.

[`SYSTEM_ADDRESS`]: ref:ethereum.forks.bogota.system_contracts.SYSTEM_ADDRESS
[`SYSTEM_CONTRACTS`]: ref:ethereum.forks.bogota.system_contracts.SYSTEM_CONTRACTS
"""  # noqa: E501

from typing import FrozenSet

from ethereum.state import Address

from .utils.hexadecimal import hex_to_address

SYSTEM_ADDRESS = hex_to_address("0xfffffffffffffffffffffffffffffffffffffffe")
BEACON_ROOTS_ADDRESS = hex_to_address(
    "0x000F3df6D732807Ef1319fB7B8bB8522d0Beac02"
)
WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS = hex_to_address(
    "0x00000961Ef480Eb55e80D19ad83579A64c007002"
)
CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS = hex_to_address(
    "0x0000BBdDc7CE488642fb579F8B00f3a590007251"
)
BUILDER_DEPOSIT_CONTRACT_ADDRESS = hex_to_address(
    "0x0000BFF46984E3725691FA540A8C7589300D8282"
)
BUILDER_EXIT_CONTRACT_ADDRESS = hex_to_address(
    "0x000064D678505AD48F8CCB093BC65613800E8282"
)
HISTORY_STORAGE_ADDRESS = hex_to_address(
    "0x0000F90827F1C53a10cb7A02335B175320002935"
)

SYSTEM_CONTRACTS: FrozenSet[Address] = frozenset(
    {
        BEACON_ROOTS_ADDRESS,
        HISTORY_STORAGE_ADDRESS,
        WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS,
        CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS,
        BUILDER_DEPOSIT_CONTRACT_ADDRESS,
        BUILDER_EXIT_CONTRACT_ADDRESS,
    }
)
"""
Accounts the protocol calls from [`SYSTEM_ADDRESS`] while processing a block.
The deposit contract is not one of them: its logs are read, but it is never
called.

[`SYSTEM_ADDRESS`]: ref:ethereum.forks.bogota.system_contracts.SYSTEM_ADDRESS
"""
