from ethereum.constantinople.trie import nibble_list_to_compact
from ethereum_optimized.constantinople.trie_utils import compact_to_nibble_list


def test_compact_to_nibble_list() -> None:
    nibble_lists = [
        b"\x00\x01\x0f\x05",
        b"\x00\x01\x0f",
        b"\x04\x02\x0a",
        b"\x01\x02\x0f\x01",
    ]
    for x in nibble_lists:
        assert compact_to_nibble_list(nibble_list_to_compact(x, True)) == (
            x,
            True,
        )
        assert compact_to_nibble_list(nibble_list_to_compact(x, False)) == (
            x,
            False,
        )
