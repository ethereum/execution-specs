"""Test the pre-allocation models used during test execution."""

from typing import Any

import pytest

from execution_testing.base_types import Address, Hash

from ...shared.address_stubs import StubAddress, StubEOA
from ..pre_alloc import AddressStubs, eoa_iterator_start

ADDR_1 = Address("0x0000000000000000000000000000000000000001")
DEPOSIT_ADDR = Address("0x00000000219ab540356cbb839cbe05303d7705fa")
TEST_PKEY = Hash(
    0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
)
TEST_ADDR = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")


@pytest.mark.parametrize(
    "input_value,expected",
    [
        pytest.param(
            "{}",
            AddressStubs({}),
            id="empty_address_stubs_string",
        ),
        pytest.param(
            '{"some_address": {"addr": "0x0000000000000000000000000000000000000001"}}',  # noqa: E501
            AddressStubs({"some_address": StubAddress(addr=ADDR_1)}),
            id="address_stubs_string_with_some_address",
        ),
    ],
)
def test_address_stubs(input_value: Any, expected: AddressStubs) -> None:
    """Test the address stubs."""
    assert AddressStubs.model_validate_json_or_file(input_value) == expected


@pytest.mark.parametrize(
    "file_name,file_contents,expected",
    [
        pytest.param(
            "empty.json",
            "{}",
            AddressStubs({}),
            id="empty_address_stubs_json",
        ),
        pytest.param(
            "one_address.json",
            '{"DEPOSIT_CONTRACT_ADDRESS": {"addr": "0x00000000219ab540356cbb839cbe05303d7705fa"}}',  # noqa: E501
            AddressStubs(
                {
                    "DEPOSIT_CONTRACT_ADDRESS": StubAddress(
                        addr=DEPOSIT_ADDR,
                    ),
                }
            ),
            id="single_address_json",
        ),
    ],
)
def test_address_stubs_from_files(
    pytester: pytest.Pytester,
    file_name: str,
    file_contents: str,
    expected: AddressStubs,
) -> None:
    """Test the address stubs."""
    filename = pytester.path.joinpath(file_name)
    filename.write_text(file_contents)

    assert AddressStubs.model_validate_json_or_file(str(filename)) == expected


def test_address_stubs_file_not_found(pytester: pytest.Pytester) -> None:
    """Test that a missing JSON file raises FileNotFoundError."""
    missing_test = pytester.path.joinpath("nonexistent.json")
    with pytest.raises(FileNotFoundError):
        AddressStubs.model_validate_json_or_file(str(missing_test))


def test_address_stubs_getitem_returns_address() -> None:
    """Verify __getitem__ returns the Address, not the stub entry."""
    stubs = AddressStubs({"label": StubAddress(addr=ADDR_1)})
    assert stubs["label"] == ADDR_1
    assert isinstance(stubs["label"], Address)


def test_address_stubs_contains() -> None:
    """Verify __contains__ checks for label presence."""
    stubs = AddressStubs({"label": StubAddress(addr=ADDR_1)})
    assert "label" in stubs
    assert "other" not in stubs


def test_address_stubs_with_pkey() -> None:
    """Parse a JSON string with a private key entry."""
    json_str = (
        '{"eoa": {"addr": "' + str(TEST_ADDR) + '", '
        '"pkey": "' + str(TEST_PKEY) + '"}}'
    )
    stubs = AddressStubs.model_validate_json_or_file(json_str)
    assert stubs["eoa"] == TEST_ADDR
    assert stubs.is_eoa("eoa")
    entry = stubs.get_entry("eoa")
    assert isinstance(entry, StubEOA)
    assert entry.pkey == TEST_PKEY


def test_address_stubs_is_eoa() -> None:
    """Verify is_eoa distinguishes entries."""
    stubs = AddressStubs(
        {
            "contract": StubAddress(addr=ADDR_1),
            "eoa": StubEOA(addr=TEST_ADDR, pkey=TEST_PKEY),
        }
    )
    assert not stubs.is_eoa("contract")
    assert stubs.is_eoa("eoa")
    assert not stubs.is_eoa("nonexistent")


class StubConfig:
    """A pytest config exposing only the options eoa_iterator_start reads."""

    def __init__(
        self, *, eoa_start: int | None = None, seed_key: str | None = None
    ) -> None:
        """Record the two option values to answer with."""
        self._options: dict[str, Any] = {
            "eoa_iterator_start": eoa_start,
            "rpc_seed_key": seed_key,
        }

    def getoption(self, name: str, default: Any = None) -> Any:
        """Mimic `pytest.Config.getoption`, defaulting unknown names."""
        return self._options.get(name, default)


SEED_KEY_A = "0x" + "01".rjust(64, "0")
SEED_KEY_B = "0x" + "02".rjust(64, "0")

# Below the secp256k1 group order, so every key counted from a start is valid.
SECP256K1N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141


def test_eoa_start_explicit_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    """An explicitly passed --eoa-start is used as given."""
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    monkeypatch.delenv("RPC_SEED_KEY", raising=False)
    config = StubConfig(eoa_start=0x1234, seed_key=SEED_KEY_A)
    assert eoa_iterator_start(config) == 0x1234  # type: ignore[arg-type]


def test_eoa_start_is_reproducible(monkeypatch: pytest.MonkeyPatch) -> None:
    """The derived default repeats, which a random one could not."""
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    monkeypatch.delenv("RPC_SEED_KEY", raising=False)
    config = StubConfig(seed_key=SEED_KEY_A)
    first = eoa_iterator_start(config)  # type: ignore[arg-type]
    assert first == eoa_iterator_start(config)  # type: ignore[arg-type]


def test_eoa_start_differs_per_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Each xdist worker gets a range of its own.

    Nothing else offsets the workers, and `session_worker_key` takes the first
    key from this iterator, so two workers sharing a start would share an
    account.
    """
    config = StubConfig(seed_key=SEED_KEY_A)
    monkeypatch.delenv("RPC_SEED_KEY", raising=False)
    starts = {}
    for worker in ("main", "gw0", "gw1", "gw2"):
        monkeypatch.setenv("PYTEST_XDIST_WORKER", worker)
        starts[worker] = eoa_iterator_start(config)  # type: ignore[arg-type]
    assert len(set(starts.values())) == len(starts)


def test_eoa_start_differs_per_seed_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Two runs funded by different seed keys never share a range."""
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    monkeypatch.delenv("RPC_SEED_KEY", raising=False)
    a = eoa_iterator_start(StubConfig(seed_key=SEED_KEY_A))  # type: ignore[arg-type]
    b = eoa_iterator_start(StubConfig(seed_key=SEED_KEY_B))  # type: ignore[arg-type]
    assert a != b


def test_eoa_start_reads_seed_key_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """RPC_SEED_KEY separates runs just as --rpc-seed-key does."""
    monkeypatch.delenv("PYTEST_XDIST_WORKER", raising=False)
    monkeypatch.setenv("RPC_SEED_KEY", SEED_KEY_A)
    from_env = eoa_iterator_start(StubConfig())  # type: ignore[arg-type]
    monkeypatch.delenv("RPC_SEED_KEY")
    from_flag = eoa_iterator_start(StubConfig(seed_key=SEED_KEY_A))  # type: ignore[arg-type]
    assert from_env == from_flag


def test_eoa_start_is_a_usable_private_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Every derived start is a valid key, with room to count upwards from.

    Zero is not a private key, and a start too close to the group order would
    walk past it partway through a run.
    """
    monkeypatch.delenv("RPC_SEED_KEY", raising=False)
    config = StubConfig(seed_key=SEED_KEY_A)
    for i in range(64):
        monkeypatch.setenv("PYTEST_XDIST_WORKER", f"gw{i}")
        start = eoa_iterator_start(config)  # type: ignore[arg-type]
        assert 0 < start
        assert start + 2**40 < SECP256K1N
