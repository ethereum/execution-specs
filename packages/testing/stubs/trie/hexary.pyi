from typing import Dict

class HexaryTrie:
    db: Dict
    root_hash: bytes

    def __init__(self, db: Dict) -> None: ...
    def set(self, key: bytes, value: bytes) -> None: ...
