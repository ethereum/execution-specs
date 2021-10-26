from ethereum.base_types import U256
from ethereum.frontier.eth_types import Address
from ethereum.utils.hexadecimal import hex_to_bytes

TestPrivateKey = (
    "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
)
TestAddress = Address(
    hex_to_bytes("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
)

Big0 = U256(0)
Big1 = U256(1)
AddrAA = Address(hex_to_bytes("0x00000000000000000000000000000000000000AA"))
AddrBB = Address(hex_to_bytes("0x00000000000000000000000000000000000000BB"))
