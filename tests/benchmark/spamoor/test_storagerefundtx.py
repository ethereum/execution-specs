import pytest

from .helpers import build_storagerefundtx_transactions


@pytest.mark.spamoor
def test_storagerefundtx_scenario_with_deploy(spamoor_config, spamoor_rpc_client):
    txs = build_storagerefundtx_transactions(
        count=spamoor_config["count"],
        slots_per_call=spamoor_config["slots_per_call"],
        gas_limit=spamoor_config["gas_limit"],
        contract_address=None,
        contract_code=None,
        deploy_gas_limit=spamoor_config["deploy_gas_limit"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config["count"] + 1

    deploy = txs[0]
    assert deploy["type"] == 2
    assert deploy["to"] == ""

    if spamoor_config["count"] > 0:
        exec_tx = txs[1]
        expected_gas = (
            spamoor_config["gas_limit"]
            if spamoor_config["gas_limit"]
            else 3_000_000
        )
        assert exec_tx["type"] == 2
        assert exec_tx["to"] == "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
        assert exec_tx["value"] == 0
        assert exec_tx["gas"] == expected_gas
        # selector(4) + uint256(32) = 36 bytes => 72 hex + "0x".
        assert len(exec_tx["data"]) == 2 + 2 * 36
        assert exec_tx["data"].startswith("0xfe0d94c1")
        # Encoded slotsPerCall matches the argument.
        encoded_slots = int(exec_tx["data"][10:], 16)
        assert encoded_slots == spamoor_config["slots_per_call"]


@pytest.mark.spamoor
def test_storagerefundtx_scenario_existing_contract(spamoor_config, spamoor_rpc_client):
    txs = build_storagerefundtx_transactions(
        count=spamoor_config["count"],
        slots_per_call=spamoor_config["slots_per_call"],
        gas_limit=0,
        contract_address="0xffffffffffffffffffffffffffffffffffffffff",
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    # No deploy tx when targeting an existing contract.
    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] > 0:
        assert txs[0]["to"] == "0xffffffffffffffffffffffffffffffffffffffff"
        assert txs[0]["data"].startswith("0xfe0d94c1")
