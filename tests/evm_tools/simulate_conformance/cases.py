"""
The request vectors the comparison runs.

Twenty-eight cases, chosen to cover one feature each and to reach the
places the specification and go-ethereum are known to disagree. Each
carries a note saying what it is for, because a vector without one is
indistinguishable from a vector that drifted.

The expected disagreements are marked `contested`, and the tests assert
that they *do* differ: a contested case that starts matching means the
note explaining why it should not has gone stale. Three of them are
places go-ethereum departs from execution-apis' own notes, one is a
pre-existing EELS/go-ethereum difference that this method did not
introduce but does make newly reachable, and one is ours.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .genesis import (
    BLOCKHASH_READER,
    CONTEXT_READER,
    EMPTY_ACCOUNT_ADDRESS,
    FORWARDER,
    GAS_BURNER,
    LOGGER,
    PAUPER,
    RECIPIENT,
    REVERTER,
    SELF_DESTRUCTOR,
    SENDER,
    THIRD_PARTY,
)

IDENTITY_PRECOMPILE = "0x0000000000000000000000000000000000000004"
SHA256_PRECOMPILE = "0x0000000000000000000000000000000000000002"
RELOCATION_TARGET = "0x0000000000000000000000000000000000001234"


def _word(value: str) -> str:
    """Left-pad a hex value to a 32-byte word."""
    return "0x" + value.removeprefix("0x").rjust(64, "0")


@dataclass
class Case:
    """One request, and why it is here."""

    name: str
    note: str
    payload: Dict[str, Any]
    reference: str = "latest"
    contested: bool = False
    """
    Whether the client is expected to answer differently.

    Set only where the difference has been traced to a decision one side
    made deliberately, and the note says which.
    """


def _call(**fields: Any) -> Dict[str, Any]:
    """Build one call object."""
    return fields


def _block(**fields: Any) -> Dict[str, Any]:
    """Build one `blockStateCall`."""
    return fields


CASES: Tuple[Case, ...] = (
    Case(
        name="simple_transfer",
        note="The smallest possible request: one transfer, no overrides.",
        payload={
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": RECIPIENT,
                                "value": "0x3e8",
                            }
                        )
                    ]
                )
            ]
        },
    ),
    Case(
        name="two_chained_calls",
        note=(
            "The second call spends what the first delivered, which is "
            "the whole difference between this method and eth_call."
        ),
        payload={
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": RECIPIENT,
                                "value": "0x3e8",
                            }
                        ),
                        _call(
                            **{
                                "from": RECIPIENT,
                                "to": THIRD_PARTY,
                                "value": "0x3e8",
                            }
                        ),
                    ]
                )
            ]
        },
    ),
    Case(
        name="logs_across_two_calls",
        note="logIndex counts across the block, not within a call.",
        payload={
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(**{"from": SENDER, "to": LOGGER}),
                        _call(**{"from": SENDER, "to": LOGGER}),
                    ]
                )
            ]
        },
    ),
    Case(
        name="block_overrides_and_context_opcodes",
        note=(
            "Every overridden field is written to storage, so a client "
            "that resolved one differently moves the state root."
        ),
        payload={
            "blockStateCalls": [
                _block(
                    blockOverrides={
                        "number": "0x64",
                        "time": "0x3e8",
                        "gasLimit": "0x1c9c380",
                        "feeRecipient": THIRD_PARTY,
                        "prevRandao": _word("0xabc"),
                        "baseFeePerGas": "0x5",
                    },
                    calls=[_call(**{"from": SENDER, "to": CONTEXT_READER})],
                )
            ]
        },
    ),
    Case(
        name="state_overrides_every_form",
        note="nonce, balance, code and stateDiff on one account.",
        payload={
            "blockStateCalls": [
                _block(
                    stateOverrides={
                        RECIPIENT: {
                            "nonce": "0x7",
                            "balance": "0xde0b6b3a7640000",
                            "code": "0x" + "00",
                            "stateDiff": {_word("0x1"): _word("0x2a")},
                        }
                    },
                    calls=[
                        _call(
                            **{"from": RECIPIENT, "to": SENDER, "value": "0x1"}
                        )
                    ],
                )
            ]
        },
    ),
    Case(
        name="two_simulated_blocks",
        note="Block two's pre-state is block one's post-state.",
        payload={
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": RECIPIENT,
                                "value": "0x3e8",
                            }
                        )
                    ]
                ),
                _block(
                    calls=[
                        _call(
                            **{
                                "from": RECIPIENT,
                                "to": THIRD_PARTY,
                                "value": "0x3e8",
                            }
                        )
                    ]
                ),
            ]
        },
    ),
    Case(
        name="revert_with_data",
        note=(
            "A revert reports code 3 with the data under error.data, and "
            "leaves returnData empty even though the frame returned bytes."
        ),
        payload={
            "blockStateCalls": [
                _block(calls=[_call(**{"from": SENDER, "to": REVERTER})])
            ]
        },
    ),
    Case(
        name="skipped_block_numbers",
        note=(
            "Jumping to block five reports the four empty blocks in "
            "between, each twelve seconds later than the last."
        ),
        payload={
            "blockStateCalls": [
                _block(
                    blockOverrides={"number": "0x5"},
                    calls=[
                        _call(
                            **{"from": SENDER, "to": RECIPIENT, "value": "0x1"}
                        )
                    ],
                )
            ]
        },
    ),
    Case(
        name="validation_on",
        note=(
            "With validation the base fee follows EIP-1559 from the "
            "parent instead of being forced to zero."
        ),
        payload={
            "validation": True,
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": RECIPIENT,
                                "value": "0x1",
                                "maxFeePerGas": "0x3b9aca00",
                                "maxPriorityFeePerGas": "0x1",
                            }
                        )
                    ]
                )
            ],
        },
    ),
    Case(
        name="trace_transfers_top_level",
        note="The documented example: one caller-level ETH movement.",
        payload={
            "traceTransfers": True,
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": RECIPIENT,
                                "value": "0x3e8",
                            }
                        )
                    ]
                )
            ],
        },
    ),
    Case(
        name="contract_as_sender",
        note=(
            "The method takes `from` at its word and permits code there, "
            "which consensus refuses outright."
        ),
        payload={
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{"from": LOGGER, "to": RECIPIENT, "value": "0x0"}
                        )
                    ]
                )
            ]
        },
    ),
    Case(
        name="intrinsic_gas_too_low",
        note="-38013: a gas limit below the intrinsic cost.",
        payload={
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{"from": SENDER, "to": RECIPIENT, "gas": "0x1"}
                        )
                    ]
                )
            ]
        },
    ),
    Case(
        name="insufficient_funds",
        note="-38014: a sender that cannot cover the value.",
        payload={
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{
                                "from": PAUPER,
                                "to": RECIPIENT,
                                "value": "0xde0b6b3a7640000",
                            }
                        )
                    ]
                )
            ]
        },
    ),
    Case(
        name="move_precompile_and_shadow_it",
        note=(
            "Identity answers at its new address, and EVM code put at "
            "the old one is what runs there now."
        ),
        payload={
            "blockStateCalls": [
                _block(
                    stateOverrides={
                        IDENTITY_PRECOMPILE: {
                            "movePrecompileToAddress": RELOCATION_TARGET,
                            "code": "0x6042600052602060206000f3",
                        }
                    },
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": RELOCATION_TARGET,
                                "input": _word("0x11"),
                            }
                        ),
                        _call(
                            **{
                                "from": SENDER,
                                "to": IDENTITY_PRECOMPILE,
                                "input": _word("0x11"),
                            }
                        ),
                    ],
                )
            ]
        },
    ),
    Case(
        name="contract_creation",
        note=(
            "A call with no `to` deploys, so the receipt and the state "
            "root have to agree about where the code landed."
        ),
        payload={
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "input": "0x600a600c600039600a6000f3"
                                "60006000526001601ff3",
                            }
                        )
                    ]
                )
            ]
        },
    ),
    Case(
        name="full_storage_replacement",
        note=(
            "`state` drops the account's existing slots where "
            "`stateDiff` merges into them."
        ),
        payload={
            "blockStateCalls": [
                _block(
                    stateOverrides={
                        CONTEXT_READER: {
                            "stateDiff": {_word("0x9"): _word("0x9")}
                        }
                    },
                    calls=[_call(**{"from": SENDER, "to": CONTEXT_READER})],
                ),
                _block(
                    stateOverrides={
                        CONTEXT_READER: {"state": {_word("0x8"): _word("0x8")}}
                    },
                    calls=[_call(**{"from": SENDER, "to": RECIPIENT})],
                ),
            ]
        },
    ),
    Case(
        name="nonce_too_low",
        note=(
            "-38010: a nonce behind the account's own. Only reachable "
            "with validation on, because that is the mode in which a "
            "nonce is checked at all."
        ),
        payload={
            "validation": True,
            "blockStateCalls": [
                _block(
                    stateOverrides={SENDER: {"nonce": "0x5"}},
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": RECIPIENT,
                                "nonce": "0x1",
                                "maxFeePerGas": "0x3b9aca00",
                            }
                        )
                    ],
                )
            ],
        },
    ),
    Case(
        name="blockhash_of_a_simulated_ancestor",
        note=(
            "The second block asks for the first block's hash, which "
            "only exists because the simulation made it."
        ),
        payload={
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{"from": SENDER, "to": RECIPIENT, "value": "0x1"}
                        )
                    ]
                ),
                _block(
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": BLOCKHASH_READER,
                                "input": _word("0x1"),
                            }
                        )
                    ]
                ),
            ]
        },
    ),
    Case(
        name="out_of_gas",
        note="-32015 per call: a halt that is not a revert.",
        payload={
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": GAS_BURNER,
                                "gas": "0x186a0",
                            }
                        )
                    ]
                )
            ]
        },
    ),
    Case(
        name="all_defaults",
        note=(
            "A call that names nothing at all, which is the payload most "
            "of the recorded corpus is made of."
        ),
        payload={"blockStateCalls": [_block(calls=[_call()])]},
    ),
    Case(
        name="block_gas_limit_exceeded",
        note="-38015: a call asking for more gas than the block has.",
        payload={
            "blockStateCalls": [
                _block(
                    blockOverrides={"gasLimit": "0x5208"},
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": RECIPIENT,
                                "gas": "0xf4240",
                            }
                        )
                    ],
                )
            ]
        },
    ),
    Case(
        name="self_destruct",
        note=(
            "A self-destruct moves the balance and, from Cancun, leaves "
            "the account behind unless it was created in this block."
        ),
        payload={
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": SELF_DESTRUCTOR,
                                "input": _word(THIRD_PARTY),
                            }
                        )
                    ]
                )
            ]
        },
    ),
    Case(
        name="return_full_transactions",
        note=(
            "The synthetic transactions rendered in full, signature "
            "fields and all."
        ),
        payload={
            "returnFullTransactions": True,
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": RECIPIENT,
                                "value": "0x3e8",
                            }
                        )
                    ]
                )
            ],
        },
    ),
    Case(
        name="trace_transfers_through_a_contract",
        note=(
            "Three movements in execution order: the caller's, the "
            "contract's log, then the transfer the contract forwarded. "
            "Only the first is visible from outside the interpreter "
            "before EIP-7708, so the specification reports two."
        ),
        contested=True,
        payload={
            "traceTransfers": True,
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": FORWARDER,
                                "value": "0x3e8",
                                "input": _word(THIRD_PARTY),
                            }
                        )
                    ]
                )
            ],
        },
    ),
    Case(
        name="move_precompile_to_itself",
        note=(
            "execution-apis names -38022 for this; go-ethereum answers "
            "-32000. The corpus vector named for -38022 records -32000, "
            "so the client is at least self-consistent."
        ),
        contested=True,
        payload={
            "blockStateCalls": [
                _block(
                    stateOverrides={
                        IDENTITY_PRECOMPILE: {
                            "movePrecompileToAddress": IDENTITY_PRECOMPILE
                        }
                    }
                )
            ]
        },
    ),
    Case(
        name="two_moves_to_the_same_address",
        note=(
            "execution-apis names -38023; go-ethereum accepts it. The "
            "corpus vector named for -38023 records a success."
        ),
        contested=True,
        payload={
            "blockStateCalls": [
                _block(
                    stateOverrides={
                        IDENTITY_PRECOMPILE: {
                            "movePrecompileToAddress": RELOCATION_TARGET
                        },
                        SHA256_PRECOMPILE: {
                            "movePrecompileToAddress": RELOCATION_TARGET
                        },
                    }
                )
            ]
        },
    ),
    Case(
        name="declared_nonce_without_validation",
        note=(
            "Measured against go-ethereum: with validation off the nonce "
            "is not checked in either direction, and the account's own "
            "nonce is what gets incremented — the declared one reaches "
            "the transaction's RLP and nothing else. The specification "
            "cannot express that. `check_transaction` compares the "
            "sender's nonce to the transaction's unconditionally, so a "
            "declared nonce that disagrees is rejected before execution "
            "begins. This is the same shape as the sender problem "
            "`asserted_sender` was introduced to solve and wants the "
            "same treatment; unlike the other contested cases it is our "
            "gap rather than a client departing from the notes."
        ),
        contested=True,
        payload={
            "blockStateCalls": [
                _block(
                    stateOverrides={SENDER: {"nonce": "0x5"}},
                    calls=[
                        _call(
                            **{"from": SENDER, "to": RECIPIENT, "nonce": "0x1"}
                        )
                    ],
                )
            ]
        },
    ),
    Case(
        name="zero_value_call_to_an_empty_account",
        note=(
            "EELS leaves the account in the trie and go-ethereum removes "
            "it, so the state root and block hash diverge. Ordinary "
            "block-execution code that this method did not introduce, "
            "but that state overrides make newly reachable."
        ),
        contested=True,
        payload={
            "blockStateCalls": [
                _block(
                    calls=[
                        _call(
                            **{
                                "from": SENDER,
                                "to": EMPTY_ACCOUNT_ADDRESS,
                                "value": "0x0",
                            }
                        )
                    ]
                )
            ]
        },
    ),
)


def contested_names() -> List[str]:
    """Return the cases expected to disagree."""
    return [case.name for case in CASES if case.contested]


__all__ = ["CASES", "Case", "contested_names"]
