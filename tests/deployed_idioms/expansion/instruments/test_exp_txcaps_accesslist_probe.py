"""
Measurement instrument: how much execution ceiling one access-list entry costs.

EIP-7981 reprices access-list entries AND charges a floor-token surcharge on
the execution side too ("on both sides of the gas-used maximum, independently
of the existing per-entry access charges", amsterdam/transactions.py:760).
Because the EIP-7825 ceiling is `TX_MAX_GAS_LIMIT - intrinsic.execution`,
every gas of that surcharge is a gas of execution capacity the transaction
can never buy back.

FAILURES ARE THE MEASUREMENT.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
)

CAP = 2**24

CANDIDATES = [
    16_762_214,  # no access list, Amsterdam intrinsic 15,000
    16_758_034,  # 1 address:        15,000 + 2,900 + 80*16
    16_753_986,  # 1 address 1 key:  + 2,000 + 128*16
    16_756_214,  # no access list, pre-2780 intrinsic 21,000
    16_753_814,  # 1 address, Osaka: 21,000 + 2,400
    16_751_914,  # 1 address 1 key, Osaka: + 1,900
]


@pytest.mark.parametrize("expected", CANDIDATES)
@pytest.mark.parametrize("keys", [0, 1], ids=["addr_only", "addr_and_key"])
@pytest.mark.valid_from("Prague")
def test_ceiling(
    state_test: StateTestFiller, pre: Alloc, keys: int, expected: int
) -> None:
    """Probe."""
    c = pre.deploy_contract(Op.SSTORE(0, Op.GAS) + Op.STOP)
    tx = Transaction(
        ty=2,
        to=c,
        gas_limit=CAP,
        access_list=[
            AccessList(
                address=Address(0xC0FFEE),
                storage_keys=[Hash(k) for k in range(keys)],
            )
        ],
        sender=pre.fund_eoa(amount=10**18),
    )
    state_test(pre=pre, post={c: Account(storage={0: expected})}, tx=tx)
