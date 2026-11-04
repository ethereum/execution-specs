"""Stubs for the leanSPHINCS bindings of EthLib."""

MESSAGE_LEN: int
PUB_KEY_SIZE: int
SEED_LEN: int
SIG_SIZE: int

def key_gen(seed: bytes) -> bytes: ...
def sign(seed: bytes, message: bytes) -> bytes: ...
def verify(public_key: bytes, message: bytes, signature: bytes) -> bool: ...
