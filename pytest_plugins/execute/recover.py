"""
Pytest plugin to recover funds from a failed remote execution.
"""
import pytest

from ethereum_test_base_types import Address, HexNumber
from ethereum_test_types import EOA


def pytest_addoption(parser):
    """
    Adds command-line options to pytest.
    """
    recover_group = parser.getgroup("execute", "Arguments defining fund recovery behavior.")
    recover_group.addoption(
        "--start-eoa-index",
        action="store",
        dest="start_eoa_index",
        type=HexNumber,
        required=True,
        default=None,
        help=("Starting private key index to use for EOA generation."),
    )
    recover_group.addoption(
        "--destination",
        action="store",
        dest="destination",
        type=Address,
        required=True,
        default=None,
        help=("Address to send the recovered funds to."),
    )
    recover_group.addoption(
        "--max-index",
        action="store",
        dest="max_index",
        type=int,
        default=100,
        help=("Maximum private key index to use for EOA generation."),
    )


@pytest.fixture(scope="session")
def destination(request: pytest.FixtureRequest) -> Address:
    """
    Get the destination address.
    """
    return request.config.option.destination


def pytest_generate_tests(metafunc: pytest.Metafunc):
    """
    Pytest hook used to dynamically generate test cases.
    """
    max_index = metafunc.config.option.max_index
    start_eoa_index = metafunc.config.option.start_eoa_index

    print(f"Generating {max_index} test cases starting from index {start_eoa_index}")

    indexes_keys = [(index, EOA(key=start_eoa_index + index)) for index in range(max_index)]

    metafunc.parametrize(
        ["index", "eoa"],
        indexes_keys,
        ids=[f"{index}-{eoa}" for index, eoa in indexes_keys],
    )
