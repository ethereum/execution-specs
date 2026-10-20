"""
Tests for the version-switchable eth protocol layer.

The wire shapes asserted here are taken from the devp2p specification
(`caps/eth.md`) and cross-checked against geth's
`eth/protocols/eth/protocol.go`.
"""

from typing import Any, Callable

import ethereum_rlp as eth_rlp
import pytest
from ethereum_types.numeric import Uint

from execution_testing.base_types import Hash

from ..protocol import (
    ETH_PROTOCOLS,
    GENESIS_FORK_ONLY,
    EthVersion,
    ForkId,
    ForkSchedule,
    ProtocolError,
    Status,
    decode_get_block_access_lists,
    decode_get_block_bodies,
    decode_get_block_headers,
    decode_hello,
    encode_hello,
    fork_id,
    highest_common_eth_version,
)
from .handshake_vectors import HELLO_WITH_EXTRA_ELEMENTS

GETH_LIKE_CAPABILITIES = [
    ("eth", 69),
    ("eth", 70),
    ("eth", 71),
    ("eth", 72),
    ("snap", 1),
]
"""What a current geth advertises (eth 69-72 plus snap/1)."""


def _decode_status(payload: bytes) -> tuple[int, int, bytes]:
    """Return the version, network identifier and genesis hash sent."""
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
        """Advertising every implemented version negotiates eth/72."""
        assert (
            highest_common_eth_version(
                tuple(ETH_PROTOCOLS), GETH_LIKE_CAPABILITIES
            )
            == 72
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
        assert (
            highest_common_eth_version((EthVersion.ETH_71,), [("eth", 69)])
            is None
        )

    def test_other_capabilities_are_ignored(self) -> None:
        """A snap capability version never joins the eth negotiation."""
        assert (
            highest_common_eth_version(
                (EthVersion.ETH_69, EthVersion.ETH_70, EthVersion.ETH_71),
                [("snap", 71)],
            )
            is None
        )


class TestHello:
    """The advertised capability set is data."""

    @pytest.mark.parametrize(
        "versions, advertised",
        [((71, 69, 70), [69, 70, 71]), ((70,), [70])],
        ids=["every-version-sorted", "single-version"],
    )
    def test_hello_advertises_one_pair_per_version(
        self, versions: tuple[int, ...], advertised: list[int]
    ) -> None:
        """Each version becomes its own ("eth", version) pair, ascending."""
        payload = encode_hello("peer/v0", b"\x01" * 64, versions)
        _, _, capabilities = decode_hello(payload)
        assert capabilities == [("eth", version) for version in advertised]

    def test_hello_declares_p2p_version_5_and_identity(self) -> None:
        """Hello carries base protocol 5 (snappy), the port and the key."""
        payload = encode_hello(
            "peer/v0", b"\x01" * 64, (69,), listen_port=30303
        )
        fields = eth_rlp.decode(payload)
        assert isinstance(fields, list) and len(fields) == 5
        assert int.from_bytes(bytes(fields[0]), "big") == 5
        assert int.from_bytes(bytes(fields[3]), "big") == 30303
        assert bytes(fields[4]) == b"\x01" * 64

    def test_a_hello_with_extra_elements_decodes(self) -> None:
        """The EIP-8 Hello decodes, its additional elements ignored."""
        assert decode_hello(HELLO_WITH_EXTRA_ELEMENTS) == (
            55,
            "kneth/v0.91/plan9",
            [("eth", 61), ("mork", 22)],
        )


MAINNET_GENESIS_HASH = bytes.fromhex(
    "d4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"
)

MAINNET_SCHEDULE = ForkSchedule(
    # Homestead, DAO, Tangerine Whistle, Spurious Dragon, Byzantium,
    # Constantinople and Petersburg (together), Istanbul, Muir Glacier,
    # Berlin, London, Arrow Glacier, Gray Glacier.
    block_numbers=(
        1150000,
        1920000,
        2463000,
        2675000,
        4370000,
        7280000,
        7280000,
        9069000,
        9200000,
        12244000,
        12965000,
        13773000,
        15050000,
    ),
    # Shanghai, Cancun, Prague, Osaka, BPO1, BPO2.
    timestamps=(
        1681338455,
        1710338135,
        1746612311,
        1764798551,
        1765290071,
        1767747671,
    ),
)

MAINNET_FORK_IDS = [
    (0, 0, "fc64ec04", 1150000),  # Unsynced
    (1149999, 0, "fc64ec04", 1150000),  # Last Frontier block
    (1150000, 0, "97c2c34c", 1920000),  # First Homestead block
    (1919999, 0, "97c2c34c", 1920000),  # Last Homestead block
    (1920000, 0, "91d1f948", 2463000),  # First DAO block
    (2462999, 0, "91d1f948", 2463000),  # Last DAO block
    (2463000, 0, "7a64da13", 2675000),  # First Tangerine block
    (2674999, 0, "7a64da13", 2675000),  # Last Tangerine block
    (2675000, 0, "3edd5b10", 4370000),  # First Spurious block
    (4369999, 0, "3edd5b10", 4370000),  # Last Spurious block
    (4370000, 0, "a00bc324", 7280000),  # First Byzantium block
    (7279999, 0, "a00bc324", 7280000),  # Last Byzantium block
    (
        7280000,
        0,
        "668db0af",
        9069000,
    ),  # Constantinople, Petersburg
    (9068999, 0, "668db0af", 9069000),  # Last Petersburg block
    (
        9069000,
        0,
        "879d6e30",
        9200000,
    ),  # First Istanbul block
    (
        9199999,
        0,
        "879d6e30",
        9200000,
    ),  # Last Istanbul block
    (9200000, 0, "e029e991", 12244000),  # First Muir Glacier block
    (12243999, 0, "e029e991", 12244000),  # Last Muir Glacier block
    (12244000, 0, "0eb440f6", 12965000),  # First Berlin block
    (12964999, 0, "0eb440f6", 12965000),  # Last Berlin block
    (12965000, 0, "b715077d", 13773000),  # First London block
    (13772999, 0, "b715077d", 13773000),  # Last London block
    (13773000, 0, "20c327fc", 15050000),  # First Arrow Glacier block
    (15049999, 0, "20c327fc", 15050000),  # Last Arrow Glacier block
    (15050000, 0, "f0afd0e3", 1681338455),  # First Gray Glacier block
    (20000000, 1681338454, "f0afd0e3", 1681338455),  # Last Gray Glacier block
    (20000000, 1681338455, "dce96c2d", 1710338135),  # First Shanghai block
    (30000000, 1710338134, "dce96c2d", 1710338135),  # Last Shanghai block
    (30000000, 1710338135, "9f3d2254", 1746612311),  # First Cancun block
    (30000000, 1746022486, "9f3d2254", 1746612311),  # Last Cancun block
    (30000000, 1746612311, "c376cf8b", 1764798551),  # First Prague block
    (30000000, 1764798550, "c376cf8b", 1764798551),  # Last Prague block
    (30000000, 1764798551, "5167e2a6", 1765290071),  # First Osaka block
    (30000000, 1765290070, "5167e2a6", 1765290071),  # Last Osaka block
    (30000000, 1765290071, "cba2a1c0", 1767747671),  # First BPO1 block
    (30000000, 1767747670, "cba2a1c0", 1767747671),  # Last BPO1 block
    (30000000, 1767747671, "07c9462e", 0),  # First BPO2 block
    (50000000, 2000000000, "07c9462e", 0),  # Future BPO2 block
]
"""
`(head number, head timestamp, fork hash, fork next)` for mainnet, from
go-ethereum's `core/forkid/forkid_test.go` (EIP-2124's own table, carried
on to BPO2).
"""

TRANSITION_GENESIS_HASH = b"\x11" * 32
"""The genesis of a transition fixture whose fork activates at t=15000."""


class TestForkId:
    """The Status fork identifier is EIP-2124's, as geth computes it."""

    @pytest.mark.parametrize(
        "head_number, head_timestamp, fork_hash, fork_next", MAINNET_FORK_IDS
    )
    def test_mainnet_fork_ids(
        self,
        head_number: int,
        head_timestamp: int,
        fork_hash: str,
        fork_next: int,
    ) -> None:
        """Every passed fork is folded in, and the next one is named."""
        assert fork_id(
            MAINNET_GENESIS_HASH,
            MAINNET_SCHEDULE,
            genesis_timestamp=0,
            head_number=head_number,
            head_timestamp=head_timestamp,
        ) == ForkId(bytes.fromhex(fork_hash), Uint(fork_next))

    @pytest.mark.parametrize(
        "identifier, encoded",
        [
            (ForkId(bytes(4), Uint(0)), "c6840000000080"),
            (
                ForkId(bytes.fromhex("deadbeef"), Uint(0xBADDCAFE)),
                "ca84deadbeef84baddcafe",
            ),
            (
                ForkId(b"\xff" * 4, Uint(2**64 - 1)),
                "ce84ffffffff88ffffffffffffffff",
            ),
        ],
    )
    def test_rlp_encoding(self, identifier: ForkId, encoded: str) -> None:
        """The EIP-2124 encoding vectors."""
        assert eth_rlp.encode(identifier).hex() == encoded

    @pytest.mark.parametrize(
        "head_timestamp, encoded",
        [
            pytest.param(14999, "c884bc4920d8823a98", id="before-the-fork"),
            pytest.param(15000, "c684597af0e280", id="at-the-fork"),
            pytest.param(30000, "c684597af0e280", id="after-the-fork"),
        ],
    )
    def test_a_transition_fixture(
        self, head_timestamp: int, encoded: str
    ) -> None:
        """
        A fork at t=15000 is the next fork until the head reaches it,
        and part of the fork hash from then on.
        """
        identifier = fork_id(
            TRANSITION_GENESIS_HASH,
            ForkSchedule(timestamps=(15000,)),
            genesis_timestamp=0,
            head_number=5,
            head_timestamp=head_timestamp,
        )
        assert eth_rlp.encode(identifier).hex() == encoded

    def test_activations_at_genesis_are_the_genesis_rule_set(self) -> None:
        """A fork at block 0 or at the genesis timestamp is no fork."""
        at_genesis = fork_id(
            TRANSITION_GENESIS_HASH,
            ForkSchedule(block_numbers=(0,), timestamps=(0, 12)),
            genesis_timestamp=12,
            head_number=5,
            head_timestamp=60,
        )
        assert at_genesis == fork_id(
            TRANSITION_GENESIS_HASH,
            GENESIS_FORK_ONLY,
            genesis_timestamp=12,
            head_number=5,
            head_timestamp=60,
        )
        assert eth_rlp.encode(at_genesis).hex() == "c684bc4920d880"


class TestStatus:
    """One Status layout since eth/69; only the declared version moves."""

    @pytest.mark.parametrize("version", sorted(ETH_PROTOCOLS))
    def test_status_declares_negotiated_version(
        self, version: EthVersion
    ) -> None:
        """The vsn field is the negotiated version, layout unchanged."""
        status = Status(
            network_id=1,
            genesis_hash=Hash(b"\xaa" * 32),
            fork_id=ForkId(b"\x00" * 4, Uint(0)),
            earliest_block=0,
            latest_block=7,
            latest_block_hash=Hash(b"\xbb" * 32),
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
        request = ETH_PROTOCOLS[EthVersion.ETH_69].decode_get_receipts(payload)
        assert request.request_id == 7
        assert request.block_hashes == [b"\xcc" * 32]
        assert request.first_block_receipt_index is None
        assert request.describe() == "receipts for 1 hashes"

    @pytest.mark.parametrize(
        "version",
        [EthVersion.ETH_70, EthVersion.ETH_71, EthVersion.ETH_72],
    )
    def test_eth70_shape(self, version: EthVersion) -> None:
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
            ETH_PROTOCOLS[EthVersion.ETH_69].decode_get_receipts(eth70_shaped)
        eth69_shaped = eth_rlp.encode([Uint(7), [b"\xcc" * 32]])
        with pytest.raises(ProtocolError):
            ETH_PROTOCOLS[EthVersion.ETH_70].decode_get_receipts(eth69_shaped)

    @pytest.mark.parametrize(
        "version,encoded",
        [
            (EthVersion.ETH_69, "c201c0"),
            (EthVersion.ETH_70, "c30180c0"),
            (EthVersion.ETH_71, "c30180c0"),
            (EthVersion.ETH_72, "c30180c0"),
        ],
    )
    def test_no_receipts_answer(
        self, version: EthVersion, encoded: str
    ) -> None:
        """[1, []] up to eth/69, then [1, lastBlockIncomplete 0, []]."""
        assert ETH_PROTOCOLS[version].encode_no_receipts(1).hex() == encoded


class TestBlockAccessLists:
    """eth/71 (EIP-8159) adds the request pair; the peer always answers."""

    def test_request_decodes(self) -> None:
        """[request-id, [hashes]], the GetBlockBodies shape."""
        payload = eth_rlp.encode([Uint(9), [b"\xdd" * 32, b"\xee" * 32]])
        request_id, hashes = decode_get_block_access_lists(payload)
        assert request_id == 9
        assert hashes == [b"\xdd" * 32, b"\xee" * 32]

    def test_eth71_onward_carries_the_request(self) -> None:
        """The pair exists from eth/71 on."""
        for version, protocol in ETH_PROTOCOLS.items():
            assert protocol.has_bals is (version >= 71)


class TestRegistry:
    """The registry is the single source of what the peer implements."""

    def test_versions_match_keys(self) -> None:
        """Each protocol object declares the version it is keyed by."""
        for version, protocol in ETH_PROTOCOLS.items():
            assert protocol.version == version


class TestMalformedRequests:
    """A request of the wrong shape is refused, never misread."""

    @pytest.mark.parametrize(
        "decode, payload",
        [
            pytest.param(
                decode_get_block_bodies,
                eth_rlp.encode([Uint(1), b"\x03\x02"]),
                id="bodies",
            ),
            pytest.param(
                decode_get_block_access_lists,
                eth_rlp.encode([Uint(1), b"\x03\x02"]),
                id="bals",
            ),
            pytest.param(
                ETH_PROTOCOLS[EthVersion.ETH_69].decode_get_receipts,
                eth_rlp.encode([Uint(1), b"\x03\x02"]),
                id="receipts-eth69",
            ),
            pytest.param(
                ETH_PROTOCOLS[EthVersion.ETH_70].decode_get_receipts,
                eth_rlp.encode([Uint(1), Uint(0), b"\x03\x02"]),
                id="receipts-eth70",
            ),
        ],
    )
    def test_a_byte_string_for_the_hash_list_is_refused(
        self, decode: Callable[[bytes], Any], payload: bytes
    ) -> None:
        """Bytes where the hash list belongs are not read as hashes."""
        with pytest.raises(ProtocolError):
            decode(payload)

    def test_a_short_hash_is_refused(self) -> None:
        """A hash entry shorter than 32 bytes is no block hash."""
        payload = eth_rlp.encode([Uint(1), [b"\x11" * 32, b"\x11" * 3]])
        with pytest.raises(ProtocolError):
            decode_get_block_bodies(payload)

    @pytest.mark.parametrize(
        "decode",
        [
            pytest.param(decode_get_block_bodies, id="bodies"),
            pytest.param(decode_get_block_access_lists, id="bals"),
        ],
    )
    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param(eth_rlp.encode(b"\x01" * 33), id="not-a-list"),
            pytest.param(eth_rlp.encode([Uint(1)]), id="one-element"),
            pytest.param(
                eth_rlp.encode([Uint(1), [b"\x11" * 32], b""]),
                id="three-elements",
            ),
            pytest.param(
                eth_rlp.encode([[b"\x01"], [b"\x11" * 32]]),
                id="list-request-id",
            ),
            pytest.param(
                eth_rlp.encode([b"\x00\x01", [b"\x11" * 32]]),
                id="leading-zero-request-id",
            ),
            pytest.param(
                eth_rlp.encode([Uint(1), [[b"\x11" * 32]]]),
                id="list-hash",
            ),
            pytest.param(
                eth_rlp.encode([Uint(1), [b"\x11" * 33]]),
                id="long-hash",
            ),
            pytest.param(
                eth_rlp.encode([Uint(1), [b"\x11" * 32]]) + b"\x00",
                id="trailing-bytes",
            ),
        ],
    )
    def test_a_malformed_hash_list_request_is_refused(
        self, decode: Callable[[bytes], Any], payload: bytes
    ) -> None:
        """Each shape `decode_to` refused is still refused."""
        with pytest.raises(ProtocolError):
            decode(payload)

    def test_requested_hashes_decode_as_hashes(self) -> None:
        """Requested hashes are block hashes from the decoder on."""
        payload = eth_rlp.encode([Uint(1), [b"\x11" * 32]])
        _, hashes = decode_get_block_bodies(payload)
        assert hashes == [Hash(b"\x11" * 32)]
        assert all(isinstance(block_hash, Hash) for block_hash in hashes)

    def test_a_byte_string_for_the_capabilities_is_refused(self) -> None:
        """A Hello whose capability list is bytes is a protocol error."""
        payload = eth_rlp.encode(
            [Uint(5), b"peer/v0", b"\x03\x02", Uint(0), b"\x01" * 64]
        )
        with pytest.raises(ProtocolError):
            decode_hello(payload)

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param(
                eth_rlp.encode([Uint(5), b"peer/v0", []])[:-1],
                id="truncated",
            ),
            pytest.param(
                eth_rlp.encode([Uint(5), b"peer/v0", []]) + b"\x00",
                id="trailing-bytes",
            ),
        ],
    )
    def test_an_undecodable_hello_is_refused(self, payload: bytes) -> None:
        """A Hello that is not one RLP item is a protocol error."""
        with pytest.raises(ProtocolError):
            decode_hello(payload)

    @pytest.mark.parametrize(
        "payload",
        [
            pytest.param(b"\xff\x00", id="undecodable"),
            pytest.param(
                eth_rlp.encode([Uint(1), [Uint(1), Uint(1), b"", b""]])[:-1],
                id="truncated",
            ),
            pytest.param(
                eth_rlp.encode([Uint(1), [Uint(1), Uint(1), b"", b""]])
                + b"\x00",
                id="trailing-bytes",
            ),
            pytest.param(
                eth_rlp.encode([b"\x00\x01", [Uint(1), Uint(1), b"", b""]]),
                id="leading-zero-request-id",
            ),
            pytest.param(
                eth_rlp.encode([Uint(1), [b"\x00\x01", Uint(1), b"", b""]]),
                id="leading-zero-origin-number",
            ),
            pytest.param(
                eth_rlp.encode([Uint(1), [Uint(1), b"\x00\x05", b"", b""]]),
                id="leading-zero-amount",
            ),
            pytest.param(
                eth_rlp.encode([Uint(1), [Uint(1), Uint(1), b"\x00", b""]]),
                id="zero-byte-skip",
            ),
            pytest.param(
                eth_rlp.encode([Uint(1), [Uint(1), Uint(1), b"", Uint(2)]]),
                id="reverse-two",
            ),
            pytest.param(
                eth_rlp.encode([Uint(1), [Uint(1), Uint(1), b"", b"\x00"]]),
                id="zero-byte-reverse",
            ),
        ],
    )
    def test_a_malformed_headers_request_is_refused(
        self, payload: bytes
    ) -> None:
        """
        A GetBlockHeaders request geth's decoder refuses is refused too:
        undecodable or trailing input, a non-canonical integer, or a
        `reverse` flag other than 0 or 1.
        """
        with pytest.raises(ProtocolError):
            decode_get_block_headers(payload)

    def test_a_hash_origin_may_start_with_a_zero_byte(self) -> None:
        """Only integers are canonical; a 32-byte hash is read whole."""
        origin = b"\x00" + b"\x11" * 31
        request = decode_get_block_headers(
            eth_rlp.encode([Uint(7), [origin, Uint(3), Uint(1), Uint(1)]])
        )
        assert request.origin_hash == Hash(origin)
        assert request.origin_number is None
        assert (request.request_id, request.amount, request.skip) == (7, 3, 1)
        assert request.reverse is True
