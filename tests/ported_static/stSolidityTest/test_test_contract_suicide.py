"""
Verify a Solidity contract that creates a child, tells it to
self-destruct, and re-calls it within the same transaction.

Ported from:
state_tests/stSolidityTest/TestContractSuicideFiller.json

@manually-enhanced: Do not overwrite. Every absolute jump target and
CODECOPY offset is a `data_placeholder` resolved from the section
lengths, so the two contracts can be edited without hand-maintaining
offsets. The original Solidity was recovered from the filler. The
ported `valid_from` was lowered from Cancun to Frontier; the tx needs
`protected=fork.supports_protected_txs()` to reach the pre-EIP-155
forks, so do not drop it.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSolidityTest/TestContractSuicideFiller.json"],
)
@pytest.mark.valid_from("Frontier")
def test_test_contract_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Create a child, destroy it, and call it again in one transaction."""
    sender = pre.fund_eoa()

    # Source: solidity
    # contract TestContract
    # {
    #     function testMethod() returns (int res)
    #     {
    #         return 225;
    #     }
    #
    #     function destroy(address sendFoundsTo)
    #     {
    #         suicide(sendFoundsTo);
    #     }
    # }
    #
    # contract main
    # {
    #    bool returnValue;
    #     function run() returns (bool)
    #     {
    #        returnValue = testContractSuicide();
    #        return returnValue;
    #     }
    #
    #     function testContractSuicide() returns (bool res)
    #     {
    #         TestContract a = new TestContract();
    #         a.destroy(block.coinbase);
    #         if (a.testMethod() == 225) //we should be able to call it
    #             return true;
    #         return false;
    #     }
    # }
    run_selector = 0xC0406226  # run()
    suicide_selector = 0xA60EEDDA  # testContractSuicide()
    test_method_selector = 0xB9C3D0A5  # testMethod()
    destroy_selector = 0xF55D9D  # destroy(address)
    test_method_result = 0xE1  # the 225 that testMethod returns
    # A selector occupies the top four bytes of the first calldata word.
    selector_shift = 2**224
    address_mask = 2**160 - 1

    def offsets(
        pairs: tuple[tuple[str, object], ...],
    ) -> dict[str, int]:
        """Map each target name to the total length of all code before it."""
        resolved: dict[str, int] = {}
        cursor = 0
        for name, section in pairs:
            cursor += len(section)  # type: ignore[arg-type]
            resolved[name] = cursor
        return resolved

    # --- TestContract: dispatcher, two entry stubs, two bodies. Its jump
    # targets are offsets into its own runtime, not the factory's code.
    child_dispatcher = (
        Op.DIV(Op.CALLDATALOAD(offset=0x0), selector_shift)
        + Op.JUMPI(
            pc=Op.PUSH1(data_placeholder="destroy_stub"),
            condition=Op.EQ(Op.DUP2, destroy_selector),
        )
        + Op.JUMPI(
            pc=Op.PUSH1(data_placeholder="test_method_stub"),
            condition=Op.EQ(test_method_selector, Op.DUP1),
        )
        + Op.STOP
    )
    destroy_stub = (
        Op.JUMPDEST
        + Op.PUSH1(data_placeholder="destroy_return")
        + Op.CALLDATALOAD(offset=0x4)
        + Op.JUMP(pc=Op.PUSH1(data_placeholder="destroy_body"))
    )
    destroy_return = Op.JUMPDEST + Op.RETURN(offset=0x0, size=0x0)
    test_method_stub = (
        Op.JUMPDEST
        + Op.PUSH1(data_placeholder="test_method_return")
        + Op.JUMP(pc=Op.PUSH1(data_placeholder="test_method_body"))
    )
    test_method_return = (
        Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
    )
    test_method_body = (
        Op.JUMPDEST + Op.PUSH1[test_method_result] + Op.SWAP1 + Op.JUMP
    )
    destroy_body = (
        Op.JUMPDEST
        + Op.SELFDESTRUCT(address=Op.AND(address_mask, Op.DUP1))
        + Op.POP
        + Op.JUMP
    )
    child_runtime = (
        child_dispatcher
        + destroy_stub
        + destroy_return
        + test_method_stub
        + test_method_return
        + test_method_body
        + destroy_body
    )
    child_targets = offsets(
        (
            ("destroy_stub", child_dispatcher),
            ("destroy_return", destroy_stub),
            ("test_method_stub", destroy_return),
            ("test_method_return", test_method_stub),
            ("test_method_body", test_method_return),
            ("destroy_body", test_method_body),
        )
    )
    child_runtime.substitute(**child_targets)

    # TestContract's creation code: return the runtime that follows it.
    child_init = (
        Op.PUSH1[len(child_runtime)]
        + Op.CODECOPY(
            dest_offset=0x0,
            offset=Op.PUSH1(data_placeholder="child_runtime_offset"),
            size=Op.DUP1,
        )
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP
    )
    child_init.substitute(child_runtime_offset=len(child_init))
    child_code = child_init + child_runtime

    # --- main: selector dispatch, then a stub per function that pushes a
    # return address, jumps into the body, and returns the result word.
    parent_dispatcher = (
        Op.DIV(Op.CALLDATALOAD(offset=0x0), selector_shift)
        + Op.JUMPI(
            pc=Op.PUSH2(data_placeholder="suicide_stub"),
            condition=Op.EQ(Op.DUP2, suicide_selector),
        )
        + Op.JUMPI(
            pc=Op.PUSH2(data_placeholder="run_stub"),
            condition=Op.EQ(run_selector, Op.DUP1),
        )
        + Op.STOP
    )
    suicide_stub = (
        Op.JUMPDEST
        + Op.PUSH2(data_placeholder="suicide_return")
        + Op.JUMP(pc=Op.PUSH2(data_placeholder="suicide_body_from_stub"))
    )
    suicide_return = (
        Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
    )
    run_stub = (
        Op.JUMPDEST
        + Op.PUSH2(data_placeholder="run_return")
        + Op.JUMP(pc=Op.PUSH2(data_placeholder="run_body"))
    )
    run_return = (
        Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.RETURN(offset=0x0, size=0x20)
    )

    # testContractSuicide(): CREATE the child, then CALL its
    # destroy(block.coinbase).
    suicide_body = (
        Op.JUMPDEST
        + Op.PUSH1[0x0] * 2
        + Op.CODECOPY(
            dest_offset=0x0,
            offset=Op.PUSH2(data_placeholder="child_code_offset"),
            size=len(child_code),
        )
        + Op.CREATE(value=0x0, offset=0x0, size=len(child_code))
        + Op.SWAP1
        + Op.POP
        + Op.AND(Op.DUP2, address_mask)
        + Op.PUSH3[destroy_selector]
        + Op.PUSH1[0x0]
        + Op.DUP1
        + Op.MSTORE(offset=Op.DUP3, value=destroy_selector * selector_shift)
        + Op.PUSH1[0x4]
        + Op.MSTORE(offset=Op.DUP2, value=Op.AND(address_mask, Op.COINBASE))
        + Op.PUSH1[0x20]
        + Op.ADD
        + Op.PUSH1[0x0] * 2
        + Op.DUP7
        + Op.SUB(Op.GAS, 0x32)
        + Op.JUMPI(
            pc=Op.PUSH2(data_placeholder="destroy_call_ok"),
            condition=Op.CALL,
        )
        + Op.STOP
    )

    # The destroyed child must still answer testMethod() in this same
    # transaction - the point of the test.
    destroy_call_ok = (
        Op.JUMPDEST
        + Op.POP * 2
        + Op.AND(Op.DUP2, address_mask)
        + Op.PUSH4[test_method_selector]
        + Op.PUSH1[0x20]
        + Op.PUSH1[0x0]
        + Op.MSTORE(
            offset=Op.DUP2, value=test_method_selector * selector_shift
        )
        + Op.PUSH1[0x4]
        + Op.PUSH1[0x0] * 2
        + Op.DUP7
        + Op.SUB(Op.GAS, 0x32)
        + Op.JUMPI(
            pc=Op.PUSH2(data_placeholder="test_call_ok"), condition=Op.CALL
        )
        + Op.STOP
    )

    # Compare the returned word against 225 and yield true / false.
    test_call_ok = (
        Op.JUMPDEST
        + Op.POP * 2
        + Op.JUMPI(
            pc=Op.PUSH2(data_placeholder="result_true"),
            condition=Op.EQ(test_method_result, Op.MLOAD(offset=0x0)),
        )
        + Op.JUMP(pc=Op.PUSH2(data_placeholder="result_false"))
    )
    result_true = (
        Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.SWAP2
        + Op.POP
        + Op.JUMP(pc=Op.PUSH2(data_placeholder="suicide_join"))
    )
    result_false = Op.JUMPDEST + Op.PUSH1[0x0] + Op.SWAP2 + Op.POP
    suicide_join = Op.JUMPDEST + Op.POP + Op.SWAP1 + Op.JUMP

    # run(): call testContractSuicide internally, then pack the bool it
    # returns into byte 0 of slot 0 (`returnValue`).
    run_body = (
        Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.PUSH2(data_placeholder="run_store")
        + Op.JUMP(pc=Op.PUSH2(data_placeholder="suicide_body_from_run"))
    )
    run_store = (
        Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.EXP(0x100, 0x0)
        + Op.AND(Op.NOT(Op.MUL(0xFF, Op.DUP2)), Op.SLOAD(key=Op.DUP2))
        + Op.SWAP1
        + Op.OR(Op.MUL, Op.DUP4)
        + Op.SWAP1
        + Op.SSTORE
        + Op.POP
        + Op.AND(Op.DIV(Op.SLOAD(key=0x0), 0x1), 0xFF)
        + Op.SWAP1
        + Op.POP
        + Op.SWAP1
        + Op.JUMP
        + Op.STOP
    )
    parent_runtime = (
        parent_dispatcher
        + suicide_stub
        + suicide_return
        + run_stub
        + run_return
        + suicide_body
        + destroy_call_ok
        + test_call_ok
        + result_true
        + result_false
        + suicide_join
        + run_body
        + run_store
    )

    # Resolve each absolute position from the sections that precede it.
    # `suicide_body` is reached from two sites, so it carries two
    # placeholder names - a name may only appear once per concatenation.
    parent_targets = offsets(
        (
            ("suicide_stub", parent_dispatcher),
            ("suicide_return", suicide_stub),
            ("run_stub", suicide_return),
            ("run_return", run_stub),
            ("suicide_body", run_return),
            ("destroy_call_ok", suicide_body),
            ("test_call_ok", destroy_call_ok),
            ("result_true", test_call_ok),
            ("result_false", result_true),
            ("suicide_join", result_false),
            ("run_body", suicide_join),
            ("run_store", run_body),
        )
    )
    suicide_body_offset = parent_targets.pop("suicide_body")
    parent_runtime.substitute(
        **parent_targets,
        suicide_body_from_stub=suicide_body_offset,
        suicide_body_from_run=suicide_body_offset,
        child_code_offset=len(parent_runtime),
    )
    factory_code = parent_runtime + child_code

    # Placeholders keep the offsets consistent with the section lengths
    # but not with their contents, so check each target still lands on a
    # JUMPDEST - that catches a section reshuffled at an unchanged size.
    child_base = len(parent_runtime) + len(child_init)
    code_bytes = bytes(factory_code)
    for name, offset in (
        list(parent_targets.items())
        + [("suicide_body", suicide_body_offset)]
        + [(f"child.{k}", child_base + v) for k, v in child_targets.items()]
    ):
        assert code_bytes[offset] == bytes(Op.JUMPDEST)[0], (
            f"{name} (0x{offset:x}) is no longer a JUMPDEST"
        )

    target = pre.deploy_contract(
        code=factory_code,
        balance=0x186A0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=run_selector.to_bytes(length=4),
        value=1,
        protected=fork.supports_protected_txs(),
    )

    post = {target: Account(storage={0: 1}, nonce=2)}

    state_test(pre=pre, post=post, tx=tx)
