import pytest

from .helpers import build_gasburnertx_transactions


@pytest.mark.spamoor
def test_gasburnertx_scenario(spamoor_config, spamoor_rpc_client):
    txs = build_gasburnertx_transactions(
        count=spamoor_config["count"],
        gas_units_to_burn=spamoor_config["gas_units_to_burn"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        deploy_gas_limit=spamoor_config["deploy_gas_limit"],
        contract_address=spamoor_config["contract_address"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    # Deploy tx + count exec txs.
    assert len(txs) == spamoor_config["count"] + 1

    deploy = txs[0]
    assert deploy["type"] == 2
    assert deploy["to"] == ""
    assert deploy["data"].startswith("0x")
    assert deploy["gas"] == spamoor_config["deploy_gas_limit"]

    if spamoor_config["count"] > 0:
        exec_tx = txs[1]
        assert exec_tx["type"] == 2
        assert exec_tx["to"] == (
            spamoor_config["contract_address"]
            or "0x3333333333333333333333333333333333333333"
        )
        assert exec_tx["gas"] == spamoor_config["gas_units_to_burn"]
        assert exec_tx["value"] == 0
        assert exec_tx["data"] == "0x00000000"
        assert "maxFeePerGas" in exec_tx
        assert "maxPriorityFeePerGas" in exec_tx
        # Second exec tx encodes txIdx=1.
        if spamoor_config["count"] > 1:
            assert txs[2]["data"] == "0x00000001"
