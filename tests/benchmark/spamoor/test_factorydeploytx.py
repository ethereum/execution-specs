import pytest
from .helpers import build_factorydeploytx_transactions


@pytest.mark.spamoor
def test_factorydeploytx_scenario_with_deploy(
    spamoor_config, spamoor_rpc_client
):
    txs = build_factorydeploytx_transactions(
        count=spamoor_config.get("count", 10),
        init_code=spamoor_config.get("init_code", "0x1234"),
        start_salt=spamoor_config.get("start_salt", 0),
        factory_address="",
        deploy_gas_limit=spamoor_config.get("deploy_gas_limit", 2000000),
        gas_limit=spamoor_config.get("gas_limit", 500000),
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config.get("count", 10) + 1

    # Check deployment tx
    assert txs[0]["type"] == 2
    assert txs[0]["to"] == ""
    assert txs[0]["gas"] == spamoor_config.get("deploy_gas_limit", 2000000)
    assert txs[0]["data"].startswith("0x60806040")

    # Check execution tx
    if spamoor_config.get("count", 10) > 0:
        assert txs[1]["to"] == "0x2222222222222222222222222222222222222222"
        # 0x4c8c9ea1 is the selector for deploy(bytes32,bytes)
        assert txs[1]["data"].startswith("0x4c8c9ea1")


@pytest.mark.spamoor
def test_factorydeploytx_scenario_no_deploy(
    spamoor_config, spamoor_rpc_client
):
    txs = build_factorydeploytx_transactions(
        count=spamoor_config.get("count", 10),
        init_code=spamoor_config.get("init_code", "0x1234"),
        start_salt=spamoor_config.get("start_salt", 0),
        factory_address="0x3333333333333333333333333333333333333333",
        deploy_gas_limit=spamoor_config.get("deploy_gas_limit", 2000000),
        gas_limit=spamoor_config.get("gas_limit", 500000),
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config.get("count", 10)

    if spamoor_config.get("count", 10) > 0:
        assert txs[0]["type"] == 2
        assert txs[0]["to"] == "0x3333333333333333333333333333333333333333"
        assert txs[0]["data"].startswith("0x4c8c9ea1")
