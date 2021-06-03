from eth1spec.rlp import BE


def test_BE() -> None:
    assert BE(0x123456) == b"\x12\x34\x56"
