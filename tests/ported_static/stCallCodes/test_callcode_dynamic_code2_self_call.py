"""
Callcode happen to a contract that is dynamically created from within the
contract (to itself).

Ported from:
state_tests/stCallCodes/callcodeDynamicCode2SelfCallFiller.json
state_tests/stDelegatecallTestHomestead/delegatecodeDynamicCode2SelfCallFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Initcode,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing import Macros as Om
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Source: lll
# (lll(seq [[0]] 1  [[20]] (ADDRESS) [[21]] (ORIGIN) [[22]] (CALLER)   )0)
CHILD_CODE = (
    Op.SSTORE(0x0, 1)
    + Op.SSTORE(0x14, Op.ADDRESS)
    + Op.SSTORE(0x15, Op.ORIGIN)
    + Op.SSTORE(0x16, Op.CALLER)
    + Op.STOP
)


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcodeDynamicCode2SelfCallFiller.json",
        "state_tests/stDelegatecallTestHomestead/delegatecodeDynamicCode2SelfCallFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "opcode", [Op.CALLCODE, Op.DELEGATECALL], ids=["callcode", "delegatecall"]
)
@pytest.mark.parametrize(
    "then_call_child", [False, True], ids=["init_only", "then_call_child"]
)
def test_callcode_dynamic_code2_self_call(
    state_test: StateTestFiller,
    pre: Alloc,
    opcode: Op,
    then_call_child: bool,
) -> None:
    """
    Create a child whose init code calls itself, while it has no code.

    Optionally the creator then calls into the deployed child.
    """
    sender = pre.fund_eoa()
    self_call = opcode(address=Op.ADDRESS, args_size=0x40, ret_size=0x40)

    if then_call_child:
        # Source: lll
        # {(seq [[10]] (CREATE 0 0 (lll(seq  [[122]] (CALLCODE 100000 <self> 0 0 64 0 64)  (RETURN 0 (lll(...)0) )  )0)   )  [[11]] (CALLCODE 100000 (SLOAD 10) 0 0 64 0 64)                   )}  # noqa: E501
        child_initcode = Initcode(
            deploy_code=CHILD_CODE, initcode_prefix=Op.SSTORE(0x7A, self_call)
        )
        target = pre.deploy_contract(
            code=Om.MSTORE(child_initcode, 0)
            + Op.SSTORE(0xA, Op.CREATE(0, 0, len(child_initcode)))
            + Op.SSTORE(
                0xB,
                opcode(address=Op.SLOAD(0xA), args_size=0x40, ret_size=0x40),
            )
            + Op.STOP,
        )
        child = compute_create_address(address=target, nonce=1)
        post = {
            target: Account(
                storage={
                    0x0: 1,
                    0xA: child,
                    0xB: 1,
                    0x14: target,
                    0x15: sender,
                    0x16: target if opcode == Op.CALLCODE else sender,
                }
            ),
            child: Account(code=CHILD_CODE, storage={0x7A: 1}),
        }
    else:
        # Source: lll
        # {  (MSTORE 0 0x604060006040600060007313136008b64ff592819b2fa6d43f2835c452020e62) (MSTORE 32 0x0186a0f2600b5533600c55000000000000000000000000000000000000000000)  (CREATE 1 0 64) }  # noqa: E501
        init_only = Op.SSTORE(0xB, self_call) + Op.SSTORE(0xC, Op.CALLER)
        target = pre.deploy_contract(
            code=Om.MSTORE(init_only, 0)
            + Op.CREATE(1, 0, len(init_only))
            + Op.STOP,
            balance=1,
        )
        child = compute_create_address(address=target, nonce=1)
        post = {
            child: Account(code=b"", storage={0xB: 1, 0xC: target}, balance=1),
        }

    tx = Transaction(sender=sender, to=target)

    state_test(pre=pre, post=post, tx=tx)
