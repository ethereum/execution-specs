import pytest

from .helpers import build_evm_fuzz_transactions


@pytest.mark.spamoor
def test_evm_fuzz_scenario(spamoor_config, spamoor_rpc_client):
    txs = build_evm_fuzz_transactions(
        count=spamoor_config["count"],
        gas_limit=spamoor_config["gas_limit"],
        min_code_size=spamoor_config["min_code_size"],
        max_code_size=spamoor_config["max_code_size"],
        payload_seed=spamoor_config["payload_seed"],
        tx_id_offset=spamoor_config["tx_id_offset"],
        fuzz_mode=spamoor_config["fuzz_mode"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=spamoor_config["from_addr"],
        private_key=spamoor_config["private_key"],
        rpc_client=spamoor_rpc_client,
    )

    assert len(txs) == spamoor_config["count"]
    if spamoor_config["count"] == 0:
        return

    expected_gas = (
        spamoor_config["gas_limit"]
        if spamoor_config["gas_limit"]
        else 1_000_000
    )
    min_cs = spamoor_config["min_code_size"]
    max_cs = spamoor_config["max_code_size"]
    zero_value_count = 0
    for tx in txs:
        assert tx["type"] == 2
        assert tx["to"] == ""  # contract creation
        assert tx["gas"] == expected_gas
        assert tx["data"].startswith("0x")
        # data is 0x + 2*bytes; each tx bytecode must fit [min, max] bytes.
        byte_len = (len(tx["data"]) - 2) // 2
        assert min_cs <= byte_len <= max_cs
        if tx["value"] == 0:
            zero_value_count += 1

    # 75/25 split: every 4th tx carries value=0. With count>=4 we must
    # see at least one zero-value tx; and at least one non-zero if count>=2.
    if spamoor_config["count"] >= 4:
        assert zero_value_count >= 1
    if spamoor_config["count"] >= 2:
        assert zero_value_count < spamoor_config["count"]


@pytest.mark.spamoor
def test_evm_fuzz_is_deterministic(spamoor_config, spamoor_rpc_client):
    kwargs = dict(
        count=max(2, spamoor_config["count"]),
        gas_limit=spamoor_config["gas_limit"],
        min_code_size=spamoor_config["min_code_size"],
        max_code_size=spamoor_config["max_code_size"],
        payload_seed="0x1234",
        tx_id_offset=0,
        fuzz_mode=spamoor_config["fuzz_mode"],
        basefee=spamoor_config["basefee"],
        tip_fee=spamoor_config["tip_fee"],
        throughput=spamoor_config["throughput"],
        from_addr=None,
        private_key=None,
        rpc_client=None,
    )
    a = build_evm_fuzz_transactions(**kwargs)
    b = build_evm_fuzz_transactions(**kwargs)
    assert [t["data"] for t in a] == [t["data"] for t in b]
