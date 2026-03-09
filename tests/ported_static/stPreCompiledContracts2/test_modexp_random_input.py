"""
Fuzzed input discovered by Guido.

Ported from:
tests/static/state_tests/stPreCompiledContracts2/modexpRandomInputFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stPreCompiledContracts2/modexpRandomInputFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, expected_post",
    [
        (
            "00000000000000000000000000000000000000000000000000000000000000e300000000000000000000000000000000000000000000000000",  # noqa: E501
            710000,
            {},
        ),
        (
            "00000000000000000000000000000000000000000000000000000000000000e300000000000000000000000000000000000000000000000000",  # noqa: E501
            7000000,
            {},
        ),
        (
            "00000000008000000000000000000000000000000000000000000000000000000000000400000000000000000000000a",  # noqa: E501
            710000,
            {},
        ),
        (
            "00000000008000000000000000000000000000000000000000000000000000000000000400000000000000000000000a",  # noqa: E501
            7000000,
            {},
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001147000000000000000000000000000000000000000000000000000000000061660350000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
            710000,
            {},
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001147000000000000000000000000000000000000000000000000000000000061660350000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
            7000000,
            {},
        ),
    ],
    ids=["case0", "case1", "case2", "case3", "case4", "case5"],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_random_input(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Fuzzed input discovered by Guido."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )
    contract = Address("0x0000000000000000000000000000000000000005")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stPreCompiledContracts2/modexpRandomInputFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Prague")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, expected_post",
    [
        (
            "00000000000000000000000000000000000000000000000000000000000000e300000000000000000000000000000000000000000000000000",  # noqa: E501
            710000,
            {},
        ),
        (
            "00000000000000000000000000000000000000000000000000000000000000e300000000000000000000000000000000000000000000000000",  # noqa: E501
            7000000,
            {},
        ),
        (
            "00000000008000000000000000000000000000000000000000000000000000000000000400000000000000000000000a",  # noqa: E501
            710000,
            {},
        ),
        (
            "00000000008000000000000000000000000000000000000000000000000000000000000400000000000000000000000a",  # noqa: E501
            7000000,
            {},
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001147000000000000000000000000000000000000000000000000000000000061660350000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
            710000,
            {},
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001147000000000000000000000000000000000000000000000000000000000061660350000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
            7000000,
            {},
        ),
    ],
    ids=["case0", "case1", "case2", "case3", "case4", "case5"],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_random_input_from_prague(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Fuzzed input discovered by Guido."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )
    contract = Address("0x0000000000000000000000000000000000000005")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stPreCompiledContracts2/modexpRandomInputFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, expected_post",
    [
        (
            "00000000000000000000000000000000000000000000000000000000000000e300000000000000000000000000000000000000000000000000",  # noqa: E501
            710000,
            {},
        ),
        (
            "00000000000000000000000000000000000000000000000000000000000000e300000000000000000000000000000000000000000000000000",  # noqa: E501
            7000000,
            {},
        ),
        (
            "00000000008000000000000000000000000000000000000000000000000000000000000400000000000000000000000a",  # noqa: E501
            710000,
            {},
        ),
        (
            "00000000008000000000000000000000000000000000000000000000000000000000000400000000000000000000000a",  # noqa: E501
            7000000,
            {},
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001147000000000000000000000000000000000000000000000000000000000061660350000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
            710000,
            {},
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001147000000000000000000000000000000000000000000000000000000000061660350000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
            7000000,
            {},
        ),
    ],
    ids=["case0", "case1", "case2", "case3", "case4", "case5"],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_random_input_from_osaka(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Fuzzed input discovered by Guido."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )
    contract = Address("0x0000000000000000000000000000000000000005")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
