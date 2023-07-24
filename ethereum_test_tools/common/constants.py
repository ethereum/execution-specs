"""
Common values used in Ethereum tests.
"""

from enum import IntEnum

TestAddress = "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b"
TestAddress2 = "0x8a0a19589531694250d570040a0c4b74576919b8"

TestPrivateKey = "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
TestPrivateKey2 = "0x9e7645d0cfd9c3a04eb7a9db59a4eb7d359f2e75c9164a9d6b9a7d54e1b6a36f"

AddrAA = "0x00000000000000000000000000000000000000aa"
AddrBB = "0x00000000000000000000000000000000000000bb"

EmptyBloom = bytes([0] * 256)
EmptyOmmersRoot = bytes.fromhex("1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347")
EmptyTrieRoot = bytes.fromhex("56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421")
EmptyHash = bytes([0] * 32)
EmptyNonce = bytes([0] * 8)
ZeroAddress = bytes([0] * 20)

HistoryStorageAddress = "0x000000000000000000000000000000000000000b"
BeaconRoot = bytes.fromhex("3e97e493f9123f7455a3be1b388db32876beea7d165a3b63528d8f9a38b7249f")


class EngineAPIError(IntEnum):
    """
    List of Engine API errors
    """

    ParseError = -32700
    InvalidRequest = -32600
    MethodNotFound = -32601
    InvalidParams = -32602
    InternalError = -32603
    ServerError = -32000
    UnknownPayload = -38001
    InvalidForkchoiceState = -38002
    InvalidPayloadAttributes = -38003
    TooLargeRequest = -38004
    UnsupportedFork = -38005
