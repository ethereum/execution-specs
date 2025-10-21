"""
abstract: Crafted tests for mainnet of
[EIP-2935: Serve historical block hashes from state](https://eips.ethereum.org/EIPS/eip-2935).
"""  # noqa: E501

import pytest
from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op

from .spec import Spec, ref_spec_2935

REFERENCE_SPEC_GIT_PATH = ref_spec_2935.git_path
REFERENCE_SPEC_VERSION = ref_spec_2935.version

pytestmark = [pytest.mark.valid_at("Prague"), pytest.mark.mainnet]


def test_eip_2935(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """Test a simple block hash request from EIP-2935 system contract."""
    check_block_number = Op.SUB(Op.NUMBER, 1)  # Parent block number
    check_contract_code = (
        Op.MSTORE(0, check_block_number)
        + Op.POP(
            Op.CALL(
                address=Spec.HISTORY_STORAGE_ADDRESS,
                args_offset=0,
                args_size=32,
                ret_offset=32,
                ret_size=32,
            )
        )
        + Op.SSTORE(0, Op.EQ(Op.MLOAD(32), Op.BLOCKHASH(check_block_number)))
    )
    check_contract_address = pre.deploy_contract(check_contract_code)
    tx = Transaction(
        to=check_contract_address,
        gas_limit=50_000,
        sender=pre.fund_eoa(),
    )
    block = Block(txs=[tx])
    blockchain_test(
        pre=pre,
        blocks=[block],
        post={
            check_contract_address: Account(storage={0: 1}),
        },
    )
