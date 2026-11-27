"""
Run CREATE/CREATE2 with init code at and one byte over the size limit.

Ported from:
state_tests/Shanghai/stEIP3860_limitmeterinitcode/createInitCodeSizeLimitFiller.yml
state_tests/Shanghai/stEIP3860_limitmeterinitcode/create2InitCodeSizeLimitFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CREATE_GAS_AT_LIMIT = {Op.CREATE: 46323, Op.CREATE2: 55539}


@pytest.mark.ported_from(
    [
        "state_tests/Shanghai/stEIP3860_limitmeterinitcode/createInitCodeSizeLimitFiller.yml",  # noqa: E501
        "state_tests/Shanghai/stEIP3860_limitmeterinitcode/create2InitCodeSizeLimitFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
# Kept before EIP-7954: the measured CREATE gas is pinned for the 0xC000
# initcode size. The raised limit is covered with fork-derived sizes by
# tests/shanghai/eip3860_initcode and
# tests/amsterdam/eip7954_increase_max_contract_size.
@pytest.mark.valid_before("EIP7954")
@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize(
    "oversize", [pytest.param(0, id="valid"), pytest.param(1, id="invalid")]
)
def test_create_init_code_size_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Op,
    oversize: int,
) -> None:
    """Run CREATE/CREATE2 with init code at and over the size limit."""
    sender = pre.fund_eoa()
    initcode_size = fork.max_initcode_size() + oversize
    salt = 0xDEADBEEF
    runtime_code = bytes(
        Op.PUSH1[0xA]
        + Op.DUP1
        + Op.PUSH1[0x0]
        + Op.DUP1
        + Op.CODECOPY
        + Op.PUSH1[0x0]
        + Op.RETURN
    )
    initcode = runtime_code.ljust(initcode_size, b"\0")

    # Store the gas the creation uses in slot 10 and its result in slot 0.
    creator_code = (
        Op.SHL(0xB0, int.from_bytes(runtime_code, "big"))
        + Op.PUSH1[0x0]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.CALLDATALOAD
    )
    if opcode == Op.CREATE2:
        creator_code += (
            Op.PUSH4[salt]
            + Op.GAS
            + Op.SWAP2
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.CREATE2
        )
    else:
        creator_code += Op.GAS + Op.SWAP1 + Op.PUSH1[0x0] + Op.DUP1 + Op.CREATE
    creator_code += (
        Op.SWAP1
        + Op.GAS
        + Op.SWAP1
        + Op.SSTORE(key=0xA, value=Op.SUB)
        + Op.PUSH1[0x0]
        + Op.SSTORE
        + Op.STOP
    )
    creator = pre.deploy_contract(code=creator_code)
    caller = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x989680,
                address=creator,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=Op.CALLDATASIZE,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.STOP,
    )
    created = compute_create_address(
        address=creator, nonce=1, salt=salt, initcode=initcode, opcode=opcode
    )

    post: dict = {sender: Account(nonce=1)}
    if oversize:
        post[caller] = Account(storage={0: 0, 1: 1})
        post[creator] = Account(storage={}, nonce=1)
        post[created] = Account.NONEXISTENT
    else:
        post[caller] = Account(storage={0: 1, 1: 1})
        post[creator] = Account(
            storage={0: created, 10: CREATE_GAS_AT_LIMIT[opcode]}, nonce=2
        )
        post[created] = Account(
            storage={}, code=runtime_code, balance=0, nonce=1
        )

    tx = Transaction(
        sender=sender,
        to=caller,
        data=Hash(initcode_size),
        gas_limit=15_000_000,
    )

    state_test(pre=pre, post=post, tx=tx)
