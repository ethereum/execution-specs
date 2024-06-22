"""
Common values used in Ethereum tests.
"""


from .base_types import Address

TestAddress = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
TestAddress2 = Address("0x8a0a19589531694250d570040a0c4b74576919b8")

TestPrivateKey = 0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
TestPrivateKey2 = 0x9E7645D0CFD9C3A04EB7A9DB59A4EB7D359F2E75C9164A9D6B9A7D54E1B6A36F

AddrAA = Address(0xAA)
AddrBB = Address(0xBB)

EmptyBloom = bytes([0] * 256)
EmptyOmmersRoot = bytes.fromhex("1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347")
EmptyTrieRoot = bytes.fromhex("56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421")
EmptyHash = bytes([0] * 32)
EmptyNonce = bytes([0] * 8)
ZeroAddress = Address(0x00)
