"""
Tests for the version-switchable eth protocol layer.

The wire shapes asserted here are taken from the devp2p specification
(`caps/eth.md`) and cross-checked against geth's
`eth/protocols/eth/protocol.go`: the Status layout is shared by every
version since eth/69, eth/70 (EIP-7975) inserts a receipt offset into
GetReceipts, and eth/71 (EIP-8159) adds the block access list request
pair.
"""

import ethereum_rlp as eth_rlp
import pytest
from ethereum_types.numeric import Uint

from ..protocol import (
    ETH_PROTOCOLS,
    GET_BLOCK_ACCESS_LISTS,
    GET_RECEIPTS,
    ProtocolError,
    Status,
    decode_get_block_access_lists,
    decode_hello,
    encode_hello,
    highest_common_eth_version,
)

GETH_LIKE_CAPABILITIES = [
    ("eth", 69),
    ("eth", 70),
    ("eth", 71),
    ("eth", 72),
    ("snap", 1),
]
"""What a current geth advertises (eth 69-72 plus snap/1)."""


def _decode_status(payload: bytes) -> tuple[int, int, bytes]:
    """
    Return the version, network identifier and genesis hash sent.

    The production peer never decodes a Status - it ignores the one the
    client sends back - so the encoder's inverse lives here, where it
    pins what each version's codec writes.
    """
    fields = eth_rlp.decode(payload)
    assert isinstance(fields, list) and len(fields) >= 3
    return (
        int.from_bytes(bytes(fields[0]), "big"),
        int.from_bytes(bytes(fields[1]), "big"),
        bytes(fields[2]),
    )


class TestNegotiation:
    """The RLPx rule: highest shared version of the shared capability."""

    def test_auto_picks_highest_implemented(self) -> None:
        """Advertising every implemented version negotiates eth/71."""
        assert (
            highest_common_eth_version(
                tuple(ETH_PROTOCOLS), GETH_LIKE_CAPABILITIES
            )
            == 71
        )

    def test_pinned_version_wins_when_shared(self) -> None:
        """A single advertised version negotiates exactly itself."""
        for version in ETH_PROTOCOLS:
            assert (
                highest_common_eth_version((version,), GETH_LIKE_CAPABILITIES)
                == version
            )

    def test_no_common_version_is_none(self) -> None:
        """A client without any shared version cannot negotiate."""
        assert highest_common_eth_version((71,), [("eth", 69)]) is None

    def test_other_capabilities_are_ignored(self) -> None:
        """A snap capability version never joins the eth negotiation."""
        assert highest_common_eth_version((69, 70, 71), [("snap", 71)]) is None


class TestHello:
    """The advertised capability set is data."""

    def test_hello_advertises_one_pair_per_version(self) -> None:
        """Each version becomes its own ("eth", version) pair."""
        payload = encode_hello("peer/v0", b"\x01" * 64, (71, 69, 70))
        _, _, capabilities = decode_hello(payload)
        assert capabilities == [("eth", 69), ("eth", 70), ("eth", 71)]

    def test_hello_single_version(self) -> None:
        """Pinning a version advertises exactly that one."""
        payload = encode_hello("peer/v0", b"\x01" * 64, (70,))
        _, _, capabilities = decode_hello(payload)
        assert capabilities == [("eth", 70)]


class TestStatus:
    """One Status layout since eth/69; only the declared version moves."""

    @pytest.mark.parametrize("version", sorted(ETH_PROTOCOLS))
    def test_status_declares_negotiated_version(self, version: int) -> None:
        """The vsn field is the negotiated version, layout unchanged."""
        status = Status(
            network_id=1,
            genesis_hash=b"\xaa" * 32,
            fork_activations=[],
            earliest_block=0,
            latest_block=7,
            latest_block_hash=b"\xbb" * 32,
        )
        encoded = ETH_PROTOCOLS[version].encode_status(status)
        assert _decode_status(encoded) == (version, 1, b"\xaa" * 32)
        # The layout is the seven-field eth/69 one for every version.
        fields = eth_rlp.decode(encoded)
        assert isinstance(fields, list) and len(fields) == 7


class TestGetReceipts:
    """eth/70 (EIP-7975) inserts the first-block receipt offset."""

    def test_eth69_shape(self) -> None:
        """[request-id, [hashes]] decodes without an offset."""
        payload = eth_rlp.encode([Uint(7), [b"\xcc" * 32]])
        request = ETH_PROTOCOLS[69].decode_get_receipts(payload)
        assert request.request_id == 7
        assert request.block_hashes == [b"\xcc" * 32]
        assert request.first_block_receipt_index is None
        assert request.describe() == "receipts for 1 hashes"

    @pytest.mark.parametrize("version", [70, 71])
    def test_eth70_shape(self, version: int) -> None:
        """[request-id, firstBlockReceiptIndex, [hashes]] from eth/70."""
        payload = eth_rlp.encode([Uint(7), Uint(3), [b"\xcc" * 32]])
        request = ETH_PROTOCOLS[version].decode_get_receipts(payload)
        assert request.request_id == 7
        assert request.block_hashes == [b"\xcc" * 32]
        assert request.first_block_receipt_index == 3
        assert request.describe() == "receipts for 1 hashes from receipt 3"

    def test_wrong_shape_for_version_is_loud(self) -> None:
        """A request in the other version's shape is a protocol error."""
        eth70_shaped = eth_rlp.encode([Uint(7), Uint(3), [b"\xcc" * 32]])
        with pytest.raises(ProtocolError):
            ETH_PROTOCOLS[69].decode_get_receipts(eth70_shaped)
        eth69_shaped = eth_rlp.encode([Uint(7), [b"\xcc" * 32]])
        with pytest.raises(ProtocolError):
            ETH_PROTOCOLS[70].decode_get_receipts(eth69_shaped)


class TestBlockAccessLists:
    """eth/71 (EIP-8159) adds the request pair; the peer stays silent."""

    def test_request_decodes(self) -> None:
        """[request-id, [hashes]], the GetBlockBodies shape."""
        payload = eth_rlp.encode([Uint(9), [b"\xdd" * 32, b"\xee" * 32]])
        request_id, hashes = decode_get_block_access_lists(payload)
        assert request_id == 9
        assert hashes == [b"\xdd" * 32, b"\xee" * 32]

    def test_only_eth71_defers_the_request(self) -> None:
        """The silence is a per-version decision, not a global one."""
        for version, protocol in ETH_PROTOCOLS.items():
            expected = version >= 71
            assert (
                GET_BLOCK_ACCESS_LISTS in protocol.unanswered_requests
            ) is expected


class TestRegistry:
    """The registry is the single source of what the peer implements."""

    def test_versions_match_keys(self) -> None:
        """Each protocol object declares the version it is keyed by."""
        for version, protocol in ETH_PROTOCOLS.items():
            assert protocol.version == version

    def test_receipts_are_never_answered(self) -> None:
        """The receipts rule holds on every implemented version."""
        for protocol in ETH_PROTOCOLS.values():
            assert protocol.unanswered_requests[GET_RECEIPTS] == "GetReceipts"
