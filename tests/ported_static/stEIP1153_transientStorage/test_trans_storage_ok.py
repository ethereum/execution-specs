"""
Test successful uses of TLOAD and TSTORE across call frames.

The original tests were written by Ori Pomerantz (qbzzt1@gmail.com).

Ported from:
state_tests/Cancun/stEIP1153_transientStorage/transStorageOKFiller.yml

@manually-enhanced: Do not overwrite. The entry-point contract was removed
so the transaction calls the contract under test directly, the single
parametrized test was split into one test per scenario that deploys only
the contracts it uses, and every contract was rewritten from the filler's
Yul with structured control flow (no hardcoded jump targets), parametrized
on its call opcodes where they vary.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Case,
    Conditional,
    Hash,
    Op,
    Opcode,
    StateTestFiller,
    Switch,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def sum_up_to(n: int) -> int:
    """Return 1 + 2 + ... + n."""
    return n * (n + 1) // 2


@pytest.mark.ported_from(
    ["state_tests/Cancun/stEIP1153_transientStorage/transStorageOKFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "call_opcode, n",
    [
        pytest.param(Op.CALL, 16, id="call_16"),
        pytest.param(Op.CALLCODE, 16, id="callcode_16"),
        pytest.param(Op.DELEGATECALL, 16, id="delegatecall_16"),
        pytest.param(Op.CALL, 256, id="call_256"),
    ],
)
def test_recursive_sum(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Opcode,
    n: int,
) -> None:
    """
    Test transient storage is shared by recursive frames of one contract.

    The contract sums 1..n by calling itself with `call_opcode`, keeping the
    loop counter in Trans[0] and the running sum in Trans[1]. Each frame
    reads the counter its caller wrote (forward availability) and the
    caller reads back the sum written by its callees (backward
    availability).
    """
    sender = pre.fund_eoa()

    summing_contract = pre.deploy_contract(
        code=Conditional(
            condition=Op.EQ(Op.CALLER, Op.ADDRESS),
            # Recursive frame: keep the counter read from Trans[0] in memory
            # (deeper frames overwrite Trans[0]). Stop once it reaches zero,
            # else add it to the sum, decrement it and recurse.
            if_true=Op.MSTORE(offset=0, value=Op.TLOAD(key=0))
            + Conditional(
                condition=Op.ISZERO(Op.MLOAD(offset=0)),
                if_true=Op.STOP,
                if_false=Op.TSTORE(
                    key=1, value=Op.ADD(Op.TLOAD(key=1), Op.MLOAD(offset=0))
                )
                + Op.TSTORE(key=0, value=Op.SUB(Op.MLOAD(offset=0), 1))
                + Conditional(
                    condition=Op.ISZERO(call_opcode(address=Op.ADDRESS)),
                    if_true=Op.REVERT(offset=0, size=0),
                ),
            ),
            # First call: seed the counter with the calldata word, start the
            # recursion with a plain CALL to self, then store the input, the
            # success of that call and the resulting sum.
            if_false=Op.SSTORE(key=1, value=Op.CALLDATALOAD(0))
            + Op.TSTORE(key=0, value=Op.CALLDATALOAD(0))
            + Op.SSTORE(key=2, value=Op.CALL(address=Op.ADDRESS))
            + Op.SSTORE(key=3, value=Op.TLOAD(key=1)),
        ),
    )

    post = {
        summing_contract: Account(storage={1: n, 2: 1, 3: sum_up_to(n)}),
    }
    tx = Transaction(sender=sender, to=summing_contract, data=Hash(n))

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/Cancun/stEIP1153_transientStorage/transStorageOKFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("n", [10, 50])
def test_callback_sum(
    state_test: StateTestFiller,
    pre: Alloc,
    n: int,
) -> None:
    """
    Test transient storage survives a call through an intervening contract.

    The summing contract recurses via a relay that calls it back. The sum
    must still accumulate in the summing contract's transient storage, and
    the relay, which records its own Trans[0] and Trans[1], must see none
    of it.
    """
    sender = pre.fund_eoa()

    # Overwrite the non-zero initial storage with the relay's own Trans[0]
    # and Trans[1] (both must be zero), then call the caller back.
    callback_relay = pre.deploy_contract(
        code=Op.SSTORE(key=0, value=Op.TLOAD(key=0))
        + Op.SSTORE(key=1, value=Op.TLOAD(key=1))
        + Op.POP(Op.CALL(address=Op.CALLER)),
        storage={0: 0x60A7, 1: 0x60A7},
    )
    sum_via_callback = pre.deploy_contract(
        code=Conditional(
            condition=Op.EQ(Op.CALLER, callback_relay),
            # Called back by the relay: keep the counter read from Trans[0]
            # in memory (deeper frames overwrite Trans[0]). Stop once it
            # reaches zero, else add it to the sum, decrement it and recurse
            # through the relay.
            if_true=Op.MSTORE(offset=0, value=Op.TLOAD(key=0))
            + Conditional(
                condition=Op.ISZERO(Op.MLOAD(offset=0)),
                if_true=Op.STOP,
                if_false=Op.TSTORE(
                    key=1, value=Op.ADD(Op.TLOAD(key=1), Op.MLOAD(offset=0))
                )
                + Op.TSTORE(key=0, value=Op.SUB(Op.MLOAD(offset=0), 1))
                + Conditional(
                    condition=Op.ISZERO(Op.CALL(address=callback_relay)),
                    if_true=Op.REVERT(offset=0, size=0),
                ),
            ),
            # First call: seed the counter with the calldata word, start the
            # recursion through the relay, then store the input, the success
            # of that call and the resulting sum.
            if_false=Op.SSTORE(key=1, value=Op.CALLDATALOAD(0))
            + Op.TSTORE(key=0, value=Op.CALLDATALOAD(0))
            + Op.SSTORE(key=2, value=Op.CALL(address=callback_relay))
            + Op.SSTORE(key=3, value=Op.TLOAD(key=1)),
        ),
    )

    post = {
        sum_via_callback: Account(storage={1: n, 2: 1, 3: sum_up_to(n)}),
        callback_relay: Account(storage={0: 0, 1: 0}),
    }
    tx = Transaction(sender=sender, to=sum_via_callback, data=Hash(n))

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/Cancun/stEIP1153_transientStorage/transStorageOKFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "first_call_opcode, second_call_opcode",
    [
        pytest.param(Op.CALL, Op.CALL, id="call"),
        pytest.param(
            Op.CALLCODE, Op.DELEGATECALL, id="callcode_and_delegatecall"
        ),
    ],
)
def test_bin_tree(
    state_test: StateTestFiller,
    pre: Alloc,
    first_call_opcode: Opcode,
    second_call_opcode: Opcode,
) -> None:
    """
    Test transient storage across sibling calls at the same depth.

    The contract calls itself twice per level, first with
    `first_call_opcode` and then with `second_call_opcode`, restoring the
    counter in Trans[0] before the second call. It counts the internal nodes
    of the tree in Trans[1], giving 2**depth - 1.
    """
    sender = pre.fund_eoa()
    depth = 6

    bin_tree = pre.deploy_contract(
        code=Conditional(
            condition=Op.EQ(Op.CALLER, Op.ADDRESS),
            # Recursive frame: keep the counter read from Trans[0] in memory
            # (deeper frames overwrite Trans[0]). Stop at a leaf (counter
            # zero), else recurse twice with the decremented counter and
            # count this node.
            if_true=Op.MSTORE(offset=0, value=Op.TLOAD(key=0))
            + Conditional(
                condition=Op.ISZERO(Op.MLOAD(offset=0)),
                if_true=Op.STOP,
                if_false=Op.TSTORE(key=0, value=Op.SUB(Op.MLOAD(offset=0), 1))
                + Conditional(
                    condition=Op.ISZERO(first_call_opcode(address=Op.ADDRESS)),
                    if_true=Op.REVERT(offset=0, size=0),
                )
                # The first subtree overwrote Trans[0]; restore it.
                + Op.TSTORE(key=0, value=Op.SUB(Op.MLOAD(offset=0), 1))
                + Conditional(
                    condition=Op.ISZERO(
                        second_call_opcode(address=Op.ADDRESS)
                    ),
                    if_true=Op.REVERT(offset=0, size=0),
                )
                + Op.TSTORE(key=1, value=Op.ADD(Op.TLOAD(key=1), 1)),
            ),
            # First call: seed the counter with the calldata word, start the
            # recursion with a plain CALL to self, then store the input, the
            # success of that call and the resulting node count.
            if_false=Op.SSTORE(key=1, value=Op.CALLDATALOAD(0))
            + Op.TSTORE(key=0, value=Op.CALLDATALOAD(0))
            + Op.SSTORE(key=2, value=Op.CALL(address=Op.ADDRESS))
            + Op.SSTORE(key=3, value=Op.TLOAD(key=1)),
        ),
    )

    post = {
        bin_tree: Account(storage={1: depth, 2: 1, 3: 2**depth - 1}),
    }
    tx = Transaction(sender=sender, to=bin_tree, data=Hash(depth))

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/Cancun/stEIP1153_transientStorage/transStorageOKFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_inherit_trans(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test CALLCODE and DELEGATECALL share the caller's transient storage.

    The checker runs an incrementer of Trans[0] with CALLCODE, DELEGATECALL
    and CALL, recording Trans[0] after each. Only the first two increment
    the checker's Trans[0]; the CALL increments the incrementer's own.
    """
    sender = pre.fund_eoa()

    transient_incrementer = pre.deploy_contract(
        code=Op.TSTORE(key=0, value=Op.ADD(Op.TLOAD(key=0), 1)),
    )
    inheritance_checker = pre.deploy_contract(
        # The initial 0x60A7 in slot 0 must be overwritten by Trans[0] = 0.
        code=Op.SSTORE(key=0, value=Op.TLOAD(key=0))
        + Op.SSTORE(key=0x11, value=Op.CALLCODE(address=transient_incrementer))
        + Op.SSTORE(key=1, value=Op.TLOAD(key=0))
        + Op.SSTORE(
            key=0x12, value=Op.DELEGATECALL(address=transient_incrementer)
        )
        + Op.SSTORE(key=2, value=Op.TLOAD(key=0))
        + Op.SSTORE(key=0x13, value=Op.CALL(address=transient_incrementer))
        + Op.SSTORE(key=3, value=Op.TLOAD(key=0)),
        storage={0: 0x60A7},
    )

    post = {
        inheritance_checker: Account(
            storage={
                # Trans[0] initially and after CALLCODE, DELEGATECALL, CALL.
                0: 0,
                1: 1,
                2: 2,
                3: 2,
                # Success of the CALLCODE, DELEGATECALL and CALL.
                0x11: 1,
                0x12: 1,
                0x13: 1,
            },
        ),
    }
    tx = Transaction(sender=sender, to=inheritance_checker, data=Hash(0))

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/Cancun/stEIP1153_transientStorage/transStorageOKFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "call_types",
    [
        # The filler's value (transStorageOKFiller.yml line 801, v14.1) is
        # 33 bytes; `:abi deepCall(uint)` only encoded the low 32 bytes, and
        # the published ethereum/tests fixture used exactly this value.
        pytest.param(
            0xF2F4F1F2F4F1F2F4F1F2F4F1F2F4F1F2F4F1F2F4F1F2F4F1F2F4F1F2F4F1F1F1,
            id="interleaved",
        ),
        pytest.param(
            0xF1F1F1F1F2F2F2F2F4F4F4F4F1F1F1F1F2F2F2F2F4F4F4F4F1F1F1F1F2F2F2F2,
            id="grouped",
        ),
        pytest.param(
            0xF1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1F1,
            id="only_call",
        ),
        pytest.param(
            0xF2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2F2,
            id="only_callcode",
        ),
        pytest.param(
            0xF4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4F4,
            id="only_delegatecall",
        ),
    ],
)
def test_deep_call(
    state_test: StateTestFiller,
    pre: Alloc,
    call_types: int,
) -> None:
    """
    Test transient storage is preserved through a deep stack of calls.

    Each byte of `call_types` is the opcode (CALL 0xF1, CALLCODE 0xF2,
    DELEGATECALL 0xF4) the contract uses to call itself at that depth,
    passing the remaining bytes on. The top frame sets Trans[0] to 1, the
    bottom frame increments it, and the top frame stores the result, 2.
    """
    sender = pre.fund_eoa()

    # A frame is at the top of the stack when not called by itself (which
    # also holds in a DELEGATECALL frame directly below the top one).
    is_top_frame = Op.ISZERO(Op.EQ(Op.ADDRESS, Op.CALLER))
    # The most significant calldata byte selects this frame's call opcode.
    call_type = Op.SHR(248, Op.CALLDATALOAD(0))
    deep_call_chain = pre.deploy_contract(
        code=Conditional(
            condition=Op.ISZERO(Op.CALLDATASIZE),
            # Bottom of the stack: increment the counter and stop.
            if_true=Op.TSTORE(key=0, value=Op.ADD(Op.TLOAD(key=0), 1))
            + Op.STOP,
        )
        + Conditional(
            condition=is_top_frame, if_true=Op.TSTORE(key=0, value=1)
        )
        # Call self with the remaining bytes (calldata without its first).
        + Op.MSTORE(offset=0, value=Op.CALLDATALOAD(0))
        + Switch(
            cases=[
                Case(
                    condition=Op.EQ(call_type, call_opcode.int()),
                    action=Op.POP(
                        call_opcode(
                            address=Op.ADDRESS,
                            args_offset=1,
                            args_size=Op.SUB(Op.CALLDATASIZE, 1),
                        )
                    ),
                )
                for call_opcode in (Op.CALL, Op.CALLCODE, Op.DELEGATECALL)
            ],
        )
        + Conditional(
            condition=is_top_frame,
            if_true=Op.SSTORE(key=0, value=Op.TLOAD(key=0)),
        ),
    )

    post = {deep_call_chain: Account(storage={0: 2})}
    tx = Transaction(sender=sender, to=deep_call_chain, data=Hash(call_types))

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["state_tests/Cancun/stEIP1153_transientStorage/transStorageOKFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
def test_static_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test STATICCALL can read transient storage but not write it.

    The checker CALLs the reader/writer to set its Trans[0], STATICCALLs it
    to read Trans[0] back, then STATICCALLs it with calldata so it tries to
    TSTORE, which must fail even though the value is unchanged.
    """
    sender = pre.fund_eoa()
    written_value = 0x60A7

    # Write Trans[0] when called with calldata, then return Trans[0].
    transient_reader_writer = pre.deploy_contract(
        code=Conditional(
            condition=Op.CALLDATASIZE,
            if_true=Op.TSTORE(key=0, value=written_value),
        )
        + Op.MSTORE(offset=0, value=Op.TLOAD(key=0))
        + Op.RETURN(offset=0, size=0x20),
    )
    static_call_checker = pre.deploy_contract(
        # A CALL with one byte of calldata sets Trans[0].
        code=Op.SSTORE(
            key=0x10,
            value=Op.CALL(
                address=transient_reader_writer, args_size=1, ret_size=0x20
            ),
        )
        + Op.SSTORE(key=0, value=Op.MLOAD(offset=0))
        # A STATICCALL without calldata reads Trans[0].
        + Op.MSTORE(offset=0, value=0)
        + Op.SSTORE(
            key=0x11,
            value=Op.STATICCALL(
                address=transient_reader_writer, ret_size=0x20
            ),
        )
        + Op.SSTORE(key=1, value=Op.MLOAD(offset=0))
        # A STATICCALL with calldata tries to write Trans[0] and fails.
        + Op.MSTORE(offset=0, value=0)
        + Op.SSTORE(
            key=0x12,
            value=Op.STATICCALL(
                address=transient_reader_writer, args_size=1, ret_size=0x20
            ),
        )
        + Op.SSTORE(key=2, value=Op.MLOAD(offset=0)),
        # Non-zero values that the failing STATICCALL overwrites with zero.
        storage={2: 0x60A7, 0x12: 0x60A7},
    )

    post = {
        static_call_checker: Account(
            storage={
                # Trans[0] returned by the CALL, the reading STATICCALL and
                # the failing writing STATICCALL.
                0: written_value,
                1: written_value,
                2: 0,
                # Success of the same three calls.
                0x10: 1,
                0x11: 1,
                0x12: 0,
            },
        ),
    }
    tx = Transaction(sender=sender, to=static_call_checker, data=Hash(0))

    state_test(pre=pre, post=post, tx=tx)
