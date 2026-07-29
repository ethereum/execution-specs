"""
Verify a STATICCALL callee observes CALLVALUE 0, never inheriting the
enclosing frame's non-zero value (delivered here by the transaction).

Ported from:
state_tests/stStaticCall/static_call_value_inherit_from_callFiller.json

@manually-enhanced: Do not overwrite. STATICCALL sees CALLVALUE 0 (never
inherited from the enclosing value-bearing frame — the ported filler's
delivery CALL is collapsed into the transaction's own value); dynamic
addresses, gas forwarded via the default Op.GAS.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CALL_VALUE = 0xA


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_call_value_inherit_from_callFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Byzantium")
def test_static_call_value_inherit_from_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """A STATICCALL callee observes CALLVALUE 0, not the caller's value."""
    # Callee returns whatever CALLVALUE it sees; under STATICCALL that is 0.
    callee = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLVALUE)
        + Op.RETURN(offset=0x0, size=0x20),
    )
    # The tx delivers CALL_VALUE to this contract, so its own CALLVALUE is
    # non-zero; the STATICCALL must still hand the callee a CALLVALUE of 0.
    caller = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                address=callee,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={1: 1},
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=caller,
        value=CALL_VALUE,
        protected=fork.supports_protected_txs(),
    )

    # slot 0: STATICCALL succeeded (1). slot 1: the returned CALLVALUE (0).
    post = {caller: Account(storage={0: 1, 1: 0})}

    state_test(pre=pre, post=post, tx=tx)
