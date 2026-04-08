"""
EIP-7928: Block-Level Access Lists.

Enforced block access lists with state locations and post-transaction state
diffs.

https://eips.ethereum.org/EIPS/eip-7928
"""

from dataclasses import replace

from ....base_fork import BaseFork
from ....gas_costs import GasCosts


class EIP7928(
    BaseFork,
    # Engine API method version bumps
    # New field `blockAccessList` in ExecutionPayload
    engine_new_payload_version_bump=True,
    engine_get_payload_version_bump=True,
):
    """EIP-7928 class."""

    @classmethod
    def header_bal_hash_required(cls) -> bool:
        """
        Header must contain block access list hash (EIP-7928).
        """
        return True

    @classmethod
    def gas_costs(cls) -> GasCosts:
        """
        The cost per block access list item is introduced in EIP-7928.
        """
        return replace(
            super(EIP7928, cls).gas_costs(),
            BLOCK_ACCESS_LIST_ITEM=2000,
        )

    @classmethod
    def empty_block_bal_item_count(cls) -> int:
        """
        Return the BAL item count for an empty EIP-7928 block.

        Four system contracts produce 15 items:
          EIP-4788 beacon roots:           1 address + 1 write + 1 read = 3
          EIP-2935 history storage:        1 address + 1 write          = 2
          EIP-7002 withdrawal requests:    1 address + 4 reads          = 5
          EIP-7251 consolidation requests: 1 address + 4 reads          = 5
        """
        return 15

    @classmethod
    def engine_execution_payload_block_access_list(cls) -> bool:
        """
        From EIP-7928, engine execution payload includes `block_access_list`
        as a parameter.
        """
        return True
