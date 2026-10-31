"""
Measurement instrument, not a corpus test (class #5, forwarding prediction).

Its FAILURES ARE THE MEASUREMENT. Each probe stores one quantity and asserts
the slot is 0, so every failure prints `want 0x0, got 0x<value>` -- the exact
number, per fork and per call shape.

`test_cls5_delta`     stores `p - child_reported`, p = g - g/64 computed
                      on-chain from `GAS` (the raw a deployed oracle network prediction).
`test_cls5_shortfall` stores `gasLimit - child_reported` for the faithful
                      `callWithExactGas` shape: gasLimit is the largest
                      value that passes the deployed pre-check
                      `(g-5000) - (g-5000)/64 > gasLimit`.

Reproduce (from engine/eels):
  ./.venv/bin/fill ../../wave1/instruments --from <Fork> --until <Fork> \
      -k "cls5 and state_test" --output /tmp/p5 -q --tb=line \
      -p no:cacheprovider
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REQUEST = 2**32  # far above any clamp, so the 63/64 clamp always binds
SLACK = 5_000  # a deployed oracle network GAS_FOR_CALL_EXACT_CHECK

# ret_offset values; each forces the CALL to pay a memory-expansion cost
# that `extend_memory.cost` folds into the forwarding budget.
SHAPES = {
    "warm_zero_value": dict(warm=True, value=0, ret=0x40),
    "cold_zero_value": dict(warm=False, value=0, ret=0x40),
    "cold_with_value": dict(warm=False, value=1, ret=0x40),
    "cold_retbuf_4kb": dict(warm=False, value=0, ret=0x1000),
    "cold_retbuf_16kb": dict(warm=False, value=0, ret=0x4000),
}


def _reporter() -> Bytecode:
    """Child: report its own `GAS` on entry."""
    return Op.MSTORE(0, Op.GAS) + Op.RETURN(0, 32)


def _prologue(target: object, warm: bool) -> Bytecode:
    code = Bytecode()
    if warm:
        code += Op.POP(Op.EXTCODESIZE(target))
    return code + Op.MSTORE(0, Op.GAS)


@pytest.mark.parametrize("shape", list(SHAPES))
@pytest.mark.valid_from("Berlin")
def test_cls5_delta(
    state_test: StateTestFiller, pre: Alloc, shape: str
) -> None:
    """Probe: p - delivered, forwarding everything."""
    cfg = SHAPES[shape]
    target = pre.deploy_contract(_reporter())
    code = _prologue(target, bool(cfg["warm"]))
    code += Op.MSTORE(0x20, Op.SUB(Op.MLOAD(0), Op.DIV(Op.MLOAD(0), 64)))
    code += Op.POP(
        Op.CALL(
            gas=REQUEST,
            address=target,
            value=cfg["value"],
            args_offset=0,
            args_size=0,
            ret_offset=cfg["ret"],
            ret_size=32,
        )
    )
    s = Storage()
    code += Op.SSTORE(
        s.store_next(0, "delta"),
        Op.SUB(Op.MLOAD(0x20), Op.MLOAD(cfg["ret"])),
    )
    caller = pre.deploy_contract(code, balance=10**18)
    tx = Transaction(
        to=caller,
        gas_limit=3_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=s)}, tx=tx)


@pytest.mark.parametrize("shape", list(SHAPES))
@pytest.mark.valid_from("Berlin")
def test_cls5_shortfall(
    state_test: StateTestFiller, pre: Alloc, shape: str
) -> None:
    """Probe: gasLimit - delivered for the deployed pre-check shape."""
    cfg = SHAPES[shape]
    target = pre.deploy_contract(_reporter())
    code = _prologue(target, bool(cfg["warm"]))
    # gasLimit = the largest value passing `(g-S) - (g-S)/64 > gasLimit`
    code += Op.MSTORE(0x20, Op.SUB(Op.MLOAD(0), SLACK))
    code += Op.MSTORE(
        0x20,
        Op.SUB(
            Op.SUB(Op.MLOAD(0x20), Op.DIV(Op.MLOAD(0x20), 64)),
            1,
        ),
    )
    code += Op.POP(
        Op.CALL(
            gas=Op.MLOAD(0x20),
            address=target,
            value=cfg["value"],
            args_offset=0,
            args_size=0,
            ret_offset=cfg["ret"],
            ret_size=32,
        )
    )
    s = Storage()
    code += Op.SSTORE(
        s.store_next(0, "shortfall"),
        Op.SUB(Op.MLOAD(0x20), Op.MLOAD(cfg["ret"])),
    )
    caller = pre.deploy_contract(code, balance=10**18)
    tx = Transaction(
        to=caller,
        gas_limit=3_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=s)}, tx=tx)


@pytest.mark.parametrize("probe", ["delta", "shortfall"])
@pytest.mark.valid_from("Prague")
def test_cls5_delegated(
    state_test: StateTestFiller, pre: Alloc, probe: str
) -> None:
    """Probe: an EIP-7702 delegated target adds a second cold access."""
    impl = pre.deploy_contract(_reporter())
    target = pre.fund_eoa(delegation=impl)

    code = Op.MSTORE(0, Op.GAS)
    if probe == "delta":
        code += Op.MSTORE(0x20, Op.SUB(Op.MLOAD(0), Op.DIV(Op.MLOAD(0), 64)))
        gas_operand: object = REQUEST
    else:
        code += Op.MSTORE(0x20, Op.SUB(Op.MLOAD(0), SLACK))
        code += Op.MSTORE(
            0x20,
            Op.SUB(Op.SUB(Op.MLOAD(0x20), Op.DIV(Op.MLOAD(0x20), 64)), 1),
        )
        gas_operand = Op.MLOAD(0x20)
    code += Op.POP(
        Op.CALL(
            gas=gas_operand,
            address=target,
            value=0,
            args_offset=0,
            args_size=0,
            ret_offset=0x40,
            ret_size=32,
        )
    )
    s = Storage()
    code += Op.SSTORE(
        s.store_next(0, probe), Op.SUB(Op.MLOAD(0x20), Op.MLOAD(0x40))
    )
    caller = pre.deploy_contract(code)
    tx = Transaction(
        to=caller,
        gas_limit=3_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={caller: Account(storage=s)}, tx=tx)
