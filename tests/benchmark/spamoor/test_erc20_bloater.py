import pytest

from .helpers import build_erc20_bloater_transactions


@pytest.mark.spamoor
def test_erc20_bloater_scenario_with_deploy(spamoor_config, spamoor_rpc_client):
    txs = build_erc20_bloater_transactions(
        count=spamoor_config["count"],
        addresses_per_tx=spamoor_config["addresses_per_tx"],
        start_address_index=spamoor_config["start_address_index"],
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

    # Deploy tx + count bloat txs.
    assert len(txs) == spamoor_config["count"] + 1

    deploy = txs[0]
    assert deploy["type"] == 2
    assert deploy["to"] == ""

    if spamoor_config["count"] > 0:
        exec_tx = txs[1]
        expected_gas = (
            spamoor_config["gas_limit"]
            if spamoor_config["gas_limit"]
            else 16_700_000
        )
        assert exec_tx["type"] == 2
        assert exec_tx["to"] == "0xdddddddddddddddddddddddddddddddddddddddd"
        assert exec_tx["value"] == 0
        assert exec_tx["gas"] == expected_gas
        # selector(4) + uint256(32) + uint256(32) = 68 bytes.
        assert len(exec_tx["data"]) == 2 + 2 * 68
        assert exec_tx["data"].startswith("0xc1926de5")

        # numAddresses argument (last 32 bytes) stays constant across txs.
        num_word = exec_tx["data"][-64:]
        assert int(num_word, 16) == spamoor_config["addresses_per_tx"]

        # startAddressIndex advances by addresses_per_tx between txs.
        if spamoor_config["count"] >= 2:
            start_a = int(txs[1]["data"][10 : 10 + 64], 16)
            start_b = int(txs[2]["data"][10 : 10 + 64], 16)
            assert start_b - start_a == spamoor_config["addresses_per_tx"]


@pytest.mark.spamoor
def test_erc20_bloater_scenario_existing_contract(spamoor_config, spamoor_rpc_client):
    txs = build_erc20_bloater_transactions(
        count=spamoor_config["count"],
        addresses_per_tx=spamoor_config["addresses_per_tx"],
        start_address_index=spamoor_config["start_address_index"],
        gas_limit=0,
        contract_address="0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
        contract_code=None,
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
        assert txs[0]["to"] == "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
        assert txs[0]["data"].startswith("0xc1926de5")
