"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stReturnDataTest
modexp_modsize0_returndatasizeFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stReturnDataTest/modexp_modsize0_returndatasizeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000101",  # noqa: E501
            {
                Address("0x4263c26963e4c1dd1cb69c116009e749f9e4eec2"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001010101",  # noqa: E501
            {
                Address("0x4263c26963e4c1dd1cb69c116009e749f9e4eec2"): Account(
                    storage={1: 1, 3: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000064000000000000000000000000000000000000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000645442ddc2b70f66c1f6d2b296c0a875be7eddd0a80958cbc7425f1899ccf90511a5c318226e48ee23f130b44dc17a691ce66be5da18b85ed7943535b205aa125e9f59294a00f05155c23e97dac6b3a00b0c63c8411bf815fc183b420b4d9dc5f715040d5c60957f52d334b843197adec58c131c907cd96059fc5adce9dda351b5df3d666fcf3eb63c46851c1816e323f2119ebdf5ef35",  # noqa: E501
            {
                Address("0x4263c26963e4c1dd1cb69c116009e749f9e4eec2"): Account(
                    storage={1: 1, 3: 100}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100f536269e59acdb356459b59f1ea6acc924650f8f05dae101a3b463d33342dcc6265d1ba9465fd0f1106b3f03a4af0a0b553e8b6ba8682584ba19c3835430ff310904a717282064031bcf9185dd172dad65305ee0e61d0c638b0a0ef0f4e51653996020c2723faea116881e25fb3d554dbc51b180052c981fc79ca93567eb6ff0e619deeb2984ae3ca232523aa5bd21ea4f8caa12cb8cd90dbafb9bd6951dcaef0fc4a74d195f5341bc6c3d7217df82597b84c4e1bbef4f2ce8c32aedbd99430f4e1a59b886c4ceb9bf7a00a415c207f3a4ccf95d5483642f95a9b240806c508c29bb48de38c8e1229257d5d807229fb3708ad6ac619b133fd7c1fe3c375f90ce55689018465a8a3d7c08097d415c702e7f57fcd6de6ea55cca75c49b835c6c90172753948fbd5dee5a74a422e3169d0cf5665ffc9198dc7f3fa502da817f1c81af0843ef5bec2ca2e8f3e24a76ac7322dab5a5bda802b247f1cf5282936cd1cb115f40e71db8d62b58c7d6c0ae7c78888987c22ff6afae345ade859a9beb127d",  # noqa: E501
            {
                Address("0x4263c26963e4c1dd1cb69c116009e749f9e4eec2"): Account(
                    storage={1: 1, 3: 256}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000f3f14010101",  # noqa: E501
            {},
        ),
    ],
    ids=["case0", "case1", "case2", "case3", "case4"],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_modsize0_returndatasize(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000000,
    )

    # Source: LLL
    # { (CALLDATACOPY 0 0 (CALLDATASIZE)) [[1]] (CALLCODE (GAS) 5 0 0 (CALLDATASIZE) 1000 32) [[2]](MLOAD 1000) [[3]](RETURNDATASIZE) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=Op.CALLDATASIZE)
            + Op.SSTORE(
                key=0x1,
                value=Op.CALLCODE(
                    gas=Op.GAS,
                    address=0x5,
                    value=0x0,
                    args_offset=0x0,
                    args_size=Op.CALLDATASIZE,
                    ret_offset=0x3E8,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x3E8))
            + Op.SSTORE(key=0x3, value=Op.RETURNDATASIZE)
            + Op.STOP
        ),
        storage={0x3: 0xFFFFFFFF},
        nonce=0,
        address=Address("0x4263c26963e4c1dd1cb69c116009e749f9e4eec2"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=10000000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stReturnDataTest/modexp_modsize0_returndatasizeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000101",  # noqa: E501
            {
                Address("0x4263c26963e4c1dd1cb69c116009e749f9e4eec2"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001010101",  # noqa: E501
            {
                Address("0x4263c26963e4c1dd1cb69c116009e749f9e4eec2"): Account(
                    storage={1: 1, 3: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000064000000000000000000000000000000000000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000645442ddc2b70f66c1f6d2b296c0a875be7eddd0a80958cbc7425f1899ccf90511a5c318226e48ee23f130b44dc17a691ce66be5da18b85ed7943535b205aa125e9f59294a00f05155c23e97dac6b3a00b0c63c8411bf815fc183b420b4d9dc5f715040d5c60957f52d334b843197adec58c131c907cd96059fc5adce9dda351b5df3d666fcf3eb63c46851c1816e323f2119ebdf5ef35",  # noqa: E501
            {
                Address("0x4263c26963e4c1dd1cb69c116009e749f9e4eec2"): Account(
                    storage={1: 1, 3: 100}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100f536269e59acdb356459b59f1ea6acc924650f8f05dae101a3b463d33342dcc6265d1ba9465fd0f1106b3f03a4af0a0b553e8b6ba8682584ba19c3835430ff310904a717282064031bcf9185dd172dad65305ee0e61d0c638b0a0ef0f4e51653996020c2723faea116881e25fb3d554dbc51b180052c981fc79ca93567eb6ff0e619deeb2984ae3ca232523aa5bd21ea4f8caa12cb8cd90dbafb9bd6951dcaef0fc4a74d195f5341bc6c3d7217df82597b84c4e1bbef4f2ce8c32aedbd99430f4e1a59b886c4ceb9bf7a00a415c207f3a4ccf95d5483642f95a9b240806c508c29bb48de38c8e1229257d5d807229fb3708ad6ac619b133fd7c1fe3c375f90ce55689018465a8a3d7c08097d415c702e7f57fcd6de6ea55cca75c49b835c6c90172753948fbd5dee5a74a422e3169d0cf5665ffc9198dc7f3fa502da817f1c81af0843ef5bec2ca2e8f3e24a76ac7322dab5a5bda802b247f1cf5282936cd1cb115f40e71db8d62b58c7d6c0ae7c78888987c22ff6afae345ade859a9beb127d",  # noqa: E501
            {
                Address("0x4263c26963e4c1dd1cb69c116009e749f9e4eec2"): Account(
                    storage={1: 1, 3: 256}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000f3f14010101",  # noqa: E501
            {},
        ),
    ],
    ids=["case0", "case1", "case2", "case3", "case4"],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_modsize0_returndatasize_from_osaka(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000000,
    )

    # Source: LLL
    # { (CALLDATACOPY 0 0 (CALLDATASIZE)) [[1]] (CALLCODE (GAS) 5 0 0 (CALLDATASIZE) 1000 32) [[2]](MLOAD 1000) [[3]](RETURNDATASIZE) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=Op.CALLDATASIZE)
            + Op.SSTORE(
                key=0x1,
                value=Op.CALLCODE(
                    gas=Op.GAS,
                    address=0x5,
                    value=0x0,
                    args_offset=0x0,
                    args_size=Op.CALLDATASIZE,
                    ret_offset=0x3E8,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x3E8))
            + Op.SSTORE(key=0x3, value=Op.RETURNDATASIZE)
            + Op.STOP
        ),
        storage={0x3: 0xFFFFFFFF},
        nonce=0,
        address=Address("0x4263c26963e4c1dd1cb69c116009e749f9e4eec2"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=10000000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
