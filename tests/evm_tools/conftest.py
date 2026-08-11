"""Pytest configuration for the evm_tools tests."""

from _pytest.config.argparsing import Parser


def pytest_addoption(parser: Parser) -> None:
    """Register the options the evm_tools tests understand."""
    parser.addoption(
        "--simulate-client",
        action="store_true",
        default=False,
        help=(
            "Compare the derived eth_simulateV1 answers against a real "
            "client. Starts go-ethereum from the hive image, so it needs "
            "Docker and that image built locally."
        ),
    )
