import pytest

from .helpers import build_storagespam_transactions


@pytest.mark.spamoor
def test_storagespam_scenario_with_deploy(spamoor_config, spamoor_rpc_client):
    txs = build_storagespam_transactions(
        count=spamoor_config["count"],
        gas_units_to_burn=spamoor_config["gas_units_to_burn"],
        reuse_contract=False,
        contract_address=spamoor_config.get("contract_address"),
        contract_code=None,
        deploy_gas_limit=spamoor_config.get("deploy_gas_limit", 2_000_000),
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
    assert deploy["data"].startswith("0x")

    if spamoor_config["count"] > 0:
        exec_tx = txs[1]
        assert exec_tx["type"] == 2
        assert exec_tx["to"] == (
            spamoor_config.get("contract_address")
            or "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        )
        assert exec_tx["value"] == 0
        assert exec_tx["gas"] == spamoor_config["gas_units_to_burn"] + 50_000
        # selector(4) + uint256(32) + uint256(32) = 68 bytes.
        assert len(exec_tx["data"]) == 2 + 2 * 68
        assert exec_tx["data"].startswith("0xfed72935")
        # Second exec tx carries seed=1, so the trailing uint256 must differ.
        if spamoor_config["count"] >= 2:
            seed_word_a = txs[1]["data"][-64:]
            seed_word_b = txs[2]["data"][-64:]
            assert seed_word_a != seed_word_b


@pytest.mark.spamoor
def test_storagespam_scenario_reuse_contract(spamoor_config, spamoor_rpc_client):
    txs = build_storagespam_transactions(
        count=spamoor_config["count"],
        gas_units_to_burn=spamoor_config["gas_units_to_burn"],
        reuse_contract=True,
        contract_address=spamoor_config.get("contract_address"),
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    # No deploy tx when reusing an existing contract.
    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] > 0:
        assert txs[0]["data"].startswith("0xfed72935")
