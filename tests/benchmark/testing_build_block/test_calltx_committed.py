"""End-to-end: commit a block of spamoor call/deploy transactions."""

from typing import Any, Callable, Dict, Sequence

import pytest
from execution_testing.base_types import Hash
from execution_testing.cli.pytest_commands.plugins.testing_build_block.testing_build_block import (  # noqa: E501
    BloatConfig,
)
from execution_testing.cli.pytest_commands.plugins.testing_build_block.tx_convert import (  # noqa: E501
    spamoor_dict_to_transaction,
)
from execution_testing.rpc import EthRPC
from execution_testing.test_types import EOA, Transaction

from tests.benchmark.spamoor.helpers import build_calltx_transactions


@pytest.mark.spamoor
@pytest.mark.testing_build_block
def test_calltx_committed(
    spamoor_config: Dict[str, Any],
    bloat_config: BloatConfig,
    bloat_signer: EOA,
    bloat_eth_rpc: EthRPC,
    bloat_commit_block: Callable[[Sequence[Transaction]], Hash],
) -> None:
    """Build contract call/deploy transactions and commit them."""
    raw_txs = build_calltx_transactions(
        count=spamoor_config["count"],
        throughput=spamoor_config["throughput"],
        amount=spamoor_config["amount"],
        basefee=spamoor_config["basefee"],
        from_addr=bloat_signer,
        private_key=bloat_config.signer_key,
        contract_code=spamoor_config["contract_code"],
        contract_address=spamoor_config["contract_address"],
        call_data=spamoor_config["call_data"],
        call_fn_sig=spamoor_config["call_fn_sig"],
        call_args=spamoor_config["call_args"],
        contract_args=spamoor_config["contract_args"],
        gas_limit=spamoor_config["gas_limit"],
        tip_fee=spamoor_config["tip_fee"],
        deploy_gas_limit=spamoor_config["deploy_gas_limit"],
        rpc_client=None,
    )
    if not raw_txs:
        pytest.skip("spamoor produced no transactions; nothing to commit")

    txs = [
        spamoor_dict_to_transaction(
            tx_dict,
            bloat_signer,
            bloat_config.chain_id,
            nonce_override=int(bloat_signer.nonce) + i,
        )
        for i, tx_dict in enumerate(raw_txs)
    ]
    prev_head = bloat_eth_rpc.get_block_by_number("latest")
    assert prev_head is not None
    prev_number = int(prev_head["number"], 16)

    new_head_hash = bloat_commit_block(txs)
    new_head = bloat_eth_rpc.get_block_by_hash(new_head_hash)
    assert new_head is not None
    assert int(new_head["number"], 16) > prev_number
