"""
Tests for the activation of
[EIP-8151: Account Code Restricted ecRecover](https://eips.ethereum.org/EIPS/eip-8151).

Before the fork, ecrecover returns any signer for the base fee alone and
reads no account. From the fork on, a recovery pays for the account access
and the code read, records the signer in the block access list, and
withholds a signer whose code is not a delegation designation.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Bytes,
    Fork,
    Op,
    Storage,
    Transaction,
)

from ...frontier.precompiles.spec import EcrecoverInput
from .spec import Spec, ref_spec_8151

REFERENCE_SPEC_GIT_PATH = ref_spec_8151.git_path
REFERENCE_SPEC_VERSION = ref_spec_8151.version

pytestmark = pytest.mark.valid_at_transition_to("EIP8151")

FORK_TIMESTAMP = 15_000
DIGEST = Bytes(b"account code restricted ecrecover").keccak256()
SENTINEL = 2**256 - 1
CONTRACT_CODE = Op.SSTORE(0, 1) + Op.STOP

# Memory layout of the callers: the 128-byte input, then the output word.
INPUT_SIZE = 128
OUTPUT_OFFSET = INPUT_SIZE


@pytest.mark.parametrize(
    "code",
    [
        pytest.param("balance-only", id="balance-only"),
        pytest.param(
            "contract", id="contract", marks=pytest.mark.pre_alloc_mutable
        ),
    ],
)
def test_ecrecover_at_transition(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    code: str,
) -> None:
    """
    Test that the account access, the code check and the block access list
    read start exactly at the fork.
    """
    if code == "balance-only":
        signer = pre.fund_eoa()
    elif code == "contract":
        signer = pre.fund_eoa(code=CONTRACT_CODE)
    else:
        raise ValueError(f"unknown code: {code}")
    v, r, s = signer.sign_digest(DIGEST)

    def recover(gas: int) -> Bytecode:
        return Op.STATICCALL(
            gas=gas,
            address=Spec.ECRECOVER,
            args_offset=0,
            args_size=INPUT_SIZE,
            ret_offset=OUTPUT_OFFSET,
            ret_size=32,
        )

    sender = pre.fund_eoa()
    blocks: list[Block] = []
    post: dict[Address, Account] = {}
    for timestamp in (FORK_TIMESTAMP - 1, FORK_TIMESTAMP, FORK_TIMESTAMP + 1):
        block_fork = fork.fork_at(timestamp=timestamp)
        activated = timestamp >= FORK_TIMESTAMP
        if activated and code == "contract":
            output_word = SENTINEL
        else:
            output_word = int.from_bytes(signer)
        if activated:
            signer_in_bal: BalAccountExpectation | None = (
                BalAccountExpectation.empty()
            )
        else:
            signer_in_bal = None

        # The base fee alone recovers the signer only before the fork.
        storage = Storage()
        caller = pre.deploy_contract(
            Op.CALLDATACOPY(0, 0, INPUT_SIZE)
            + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
            + Op.SSTORE(
                storage.store_next(int(not activated), "base_fee_call"),
                recover(
                    block_fork.ecrecover_gas(
                        recovered=False, address_warm=False
                    )
                ),
            )
            + Op.SSTORE(
                storage.store_next(1, "cold_call"),
                recover(
                    block_fork.ecrecover_gas(
                        recovered=True, address_warm=False
                    )
                ),
            )
            + Op.SSTORE(
                storage.store_next(output_word, "output"),
                Op.MLOAD(OUTPUT_OFFSET),
            ),
            storage=storage.canary(),
        )
        blocks.append(
            Block(
                timestamp=timestamp,
                txs=[
                    Transaction(
                        to=caller,
                        data=EcrecoverInput(
                            msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s
                        ),
                        sender=sender,
                    )
                ],
                expected_block_access_list=BlockAccessListExpectation(
                    account_expectations={signer: signer_in_bal}
                ),
            )
        )
        post[caller] = Account(storage=storage)

    blockchain_test(pre=pre, blocks=blocks, post=post)
