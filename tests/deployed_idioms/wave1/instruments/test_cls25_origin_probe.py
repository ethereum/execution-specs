"""
Measurement instrument for class #25 (`tx.origin == msg.sender` as an "a
wallet called me directly" test). **ITS FAILURES ARE THE MEASUREMENT.**
Every param asserts 0, so the mismatch prints the real value.

Everything the gate can observe is packed into ONE slot, because
`Storage` raises on its first mismatch and a multi-slot probe only ever
reveals its lowest unexpected slot:

    bit  0        EQ(ORIGIN, CALLER)      what the deployed gate tests
    bits 8..23    EXTCODESIZE(CALLER)     the other deployed EOA test (#22)
    bit  24       EQ(CALLER, tx sender)
    bit  25       EQ(ORIGIN, tx sender)

Shapes measured:

    direct          EOA -> gate                     (the sound positive)
    via_call        EOA -> relay -(CALL)-> gate     (the sound negative)
    via_delegate    EOA -> proxy -(DELEGATECALL)-> gate
    entrypoint      EOA -> entrypoint -> account -> gate   (4337 shape)
    delegated_eoa   type-4 self-sponsored: EOA(code) -> gate

Reproduce (from tests/deployed_idioms/):
  python3 tools/locked_fill.py tests/tools --from <Fork> --until <Fork> \
      -k cls25 --output /tmp/cls25probe -q --tb=line -p no:cacheprovider
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Bytecode,
    Op,
    StateTestFiller,
    Transaction,
)

SLOT_PACKED = 0x01


def _gate(sender: Address) -> Bytecode:
    """Pack every observable identity reading into one word."""
    return (
        Op.SSTORE(
            SLOT_PACKED,
            Op.OR(
                Op.OR(
                    Op.EQ(Op.ORIGIN, Op.CALLER),
                    Op.SHL(8, Op.EXTCODESIZE(Op.CALLER)),
                ),
                Op.OR(
                    Op.SHL(24, Op.EQ(Op.CALLER, sender)),
                    Op.SHL(25, Op.EQ(Op.ORIGIN, sender)),
                ),
            ),
        )
        + Op.STOP
    )


SHAPES = ["direct", "via_call", "via_delegate", "entrypoint"]


@pytest.mark.parametrize("shape", SHAPES)
@pytest.mark.valid_from("Berlin")
def test_cls25_shapes(
    state_test: StateTestFiller, pre: Alloc, shape: str
) -> None:
    """Probe: what the gate sees for each call shape."""
    sender = pre.fund_eoa()
    gate = pre.deploy_contract(_gate(sender))

    if shape == "direct":
        target = gate
        observed = gate
    elif shape == "via_call":
        target = pre.deploy_contract(
            Op.POP(Op.CALL(gas=Op.GAS, address=gate)) + Op.STOP
        )
        observed = gate
    elif shape == "via_delegate":
        # the gate's code runs in the proxy's storage, so read the proxy
        target = pre.deploy_contract(
            Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=gate)) + Op.STOP
        )
        observed = target
    else:  # entrypoint: bundler EOA -> entrypoint -> smart account -> gate
        account = pre.deploy_contract(
            Op.POP(Op.CALL(gas=Op.GAS, address=gate)) + Op.STOP
        )
        target = pre.deploy_contract(
            Op.POP(Op.CALL(gas=Op.GAS, address=account)) + Op.STOP
        )
        observed = gate

    tx = Transaction(to=target, state_gas_reservoir=0, sender=sender)
    state_test(
        pre=pre,
        post={observed: Account(storage={SLOT_PACKED: 0})},
        tx=tx,
    )


@pytest.mark.valid_from("Prague")
def test_cls25_delegated_eoa(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Probe: a self-sponsored type-4 transaction whose delegated code calls
    the gate. ORIGIN and CALLER are both the signer, so the gate reads
    "called directly by a wallet" -- while the call was made by code.
    """
    signer = pre.fund_eoa()
    gate = pre.deploy_contract(_gate(signer))
    impl = pre.deploy_contract(
        Op.POP(Op.CALL(gas=Op.GAS, address=gate)) + Op.STOP
    )
    tx = Transaction(
        to=signer,
        state_gas_reservoir=0,
        sender=signer,
        authorization_list=[
            AuthorizationTuple(address=impl, nonce=1, signer=signer)
        ],
    )
    state_test(
        pre=pre,
        post={gate: Account(storage={SLOT_PACKED: 0})},
        tx=tx,
    )
