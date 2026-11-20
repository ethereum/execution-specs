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


NEGOTIATIONS = {
    "highest-shared": (tuple(ETH_PROTOCOLS), GETH_LIKE_CAPABILITIES, 72),
    **{
        f"pinned-{int(version)}": ((version,), GETH_LIKE_CAPABILITIES, version)
        for version in ETH_PROTOCOLS
    },
    "no-common-version": ((EthVersion.ETH_71,), [("eth", 69)], None),
    # A snap capability version never joins the eth negotiation.
    "other-capability": (
        (EthVersion.ETH_69, EthVersion.ETH_70, EthVersion.ETH_71),
        [("snap", 71)],
        None,
    ),
}


class TestNegotiation:
    """The RLPx rule: highest shared version of the shared capability."""

    @pytest.mark.parametrize(
        "local,remote,negotiated",
        NEGOTIATIONS.values(),
        ids=NEGOTIATIONS.keys(),
    )
    def test_the_highest_shared_eth_version_wins(
        self,
        local: tuple[EthVersion, ...],
        remote: list[tuple[str, int]],
        negotiated: int | None,
    ) -> None:
        """Every shared version counts, any other capability does not."""
        assert highest_common_eth_version(local, remote) == negotiated


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


HASH_LIST_SHAPES = {
    "not-a-list": eth_rlp.encode(b"\x01" * 33),
    "one-element": eth_rlp.encode([Uint(1)]),
    "three-elements": eth_rlp.encode([Uint(1), [b"\x11" * 32], b""]),
    "list-request-id": eth_rlp.encode([[b"\x01"], [b"\x11" * 32]]),
    "leading-zero-request-id": eth_rlp.encode([b"\x00\x01", [b"\x11" * 32]]),
    "list-hash": eth_rlp.encode([Uint(1), [[b"\x11" * 32]]]),
    "long-hash": eth_rlp.encode([Uint(1), [b"\x11" * 33]]),
    "short-hash": eth_rlp.encode([Uint(1), [b"\x11" * 32, b"\x11" * 3]]),
    "byte-string-hashes": eth_rlp.encode([Uint(1), b"\x03\x02"]),
    "trailing-bytes": eth_rlp.encode([Uint(1), [b"\x11" * 32]]) + b"\x00",
}
"""Shapes `decode_to` refuses for a `[request-id, [hash, ...]]` request."""

HEADERS_QUERY = (Uint(1), Uint(1), b"", b"")
"""A well formed GetBlockHeaders query: origin 1, one header, forward."""

MALFORMED_MESSAGES = [
    *(
        pytest.param(decode, payload, id=f"{name}-{shape}")
        for name, decode in (
            ("bodies", decode_get_block_bodies),
            ("bals", decode_get_block_access_lists),
        )
        for shape, payload in HASH_LIST_SHAPES.items()
    ),
    pytest.param(
        ETH_PROTOCOLS[EthVersion.ETH_69].decode_get_receipts,
        eth_rlp.encode([Uint(1), b"\x03\x02"]),
        id="receipts-eth69-byte-string-hashes",
    ),
    pytest.param(
        ETH_PROTOCOLS[EthVersion.ETH_70].decode_get_receipts,
        eth_rlp.encode([Uint(1), Uint(0), b"\x03\x02"]),
        id="receipts-eth70-byte-string-hashes",
    ),
    pytest.param(
        decode_hello,
        eth_rlp.encode(
            [Uint(5), b"peer/v0", b"\x03\x02", Uint(0), b"\x01" * 64]
        ),
        id="hello-byte-string-capabilities",
    ),
    pytest.param(
        decode_hello,
        eth_rlp.encode([Uint(5), b"peer/v0", []])[:-1],
        id="hello-truncated",
    ),
    pytest.param(
        decode_hello,
        eth_rlp.encode([Uint(5), b"peer/v0", []]) + b"\x00",
        id="hello-trailing-bytes",
    ),
    *(
        pytest.param(decode_get_block_headers, payload, id=f"headers-{name}")
        for name, payload in {
            "undecodable": b"\xff\x00",
            "truncated": eth_rlp.encode([Uint(1), HEADERS_QUERY])[:-1],
            "trailing-bytes": eth_rlp.encode([Uint(1), HEADERS_QUERY])
            + b"\x00",
            "leading-zero-request-id": eth_rlp.encode(
                [b"\x00\x01", HEADERS_QUERY]
            ),
            "leading-zero-origin-number": eth_rlp.encode(
                [Uint(1), [b"\x00\x01", Uint(1), b"", b""]]
            ),
            "leading-zero-amount": eth_rlp.encode(
                [Uint(1), [Uint(1), b"\x00\x05", b"", b""]]
            ),
            "zero-byte-skip": eth_rlp.encode(
                [Uint(1), [Uint(1), Uint(1), b"\x00", b""]]
            ),
            "reverse-two": eth_rlp.encode(
                [Uint(1), [Uint(1), Uint(1), b"", Uint(2)]]
            ),
            "zero-byte-reverse": eth_rlp.encode(
                [Uint(1), [Uint(1), Uint(1), b"", b"\x00"]]
            ),
        }.items()
    ),
]
"""
Every request and Hello shape a decoder must refuse. GetBlockHeaders
refuses what geth's decoder refuses: undecodable or trailing input, a
non-canonical integer, or a `reverse` flag other than 0 or 1.
"""


class TestMalformedRequests:
    """A request of the wrong shape is refused, never misread."""

    @pytest.mark.parametrize("decode, payload", MALFORMED_MESSAGES)
    def test_a_malformed_message_is_refused(
        self, decode: Callable[[bytes], Any], payload: bytes
    ) -> None:
        """The decoder raises `ProtocolError` rather than misread it."""
        with pytest.raises(ProtocolError):
            decode(payload)

    def test_requested_hashes_decode_as_hashes(self) -> None:
        """Requested hashes are block hashes from the decoder on."""
        payload = eth_rlp.encode([Uint(1), [b"\x11" * 32]])
        _, hashes = decode_get_block_bodies(payload)
        assert hashes == [Hash(b"\x11" * 32)]
        assert all(isinstance(block_hash, Hash) for block_hash in hashes)

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
