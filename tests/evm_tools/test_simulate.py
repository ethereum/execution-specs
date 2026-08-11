"""
Tests for deriving `eth_simulateV1` from the specification.

The values pinned here were measured against go-ethereum; the harness
under `tests/evm_tools/simulate_conformance/` reproduces that comparison
against a live client. What is worth locking down offline is the part
that has to be exactly right for a client to agree at all: the synthetic
transaction a `blockStateCall` turns into, since its hash feeds the
transactions root and therefore the block hash the response reports.
"""

from typing import Any, Dict, List

import pytest
from ethereum_types.bytes import Bytes, Bytes20
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32
from ethereum.state import EMPTY_CODE_HASH, Account
from ethereum.state_mpt import State, set_account, store_code
from ethereum_spec_tools.evm_tools.simulate import (
    BaseBlock,
    EthSimulate,
    SimulatedBlock,
)
from ethereum_spec_tools.evm_tools.simulate.context import (
    resolve_simulate_fork,
)
from ethereum_spec_tools.evm_tools.simulate.errors import SimulateError
from ethereum_spec_tools.evm_tools.simulate.payload import SimulatePayload
from ethereum_spec_tools.evm_tools.simulate.transfers import (
    TRANSFER_LOG_EMITTER,
)

SENDER = "0xc000000000000000000000000000000000000000"
RECIPIENT = "0xc100000000000000000000000000000000000000"
THIRD_PARTY = "0xc200000000000000000000000000000000000000"

GAS_LIMIT = 0x2FEFD8
"""Matches the genesis the go-ethereum comparison ran against."""

GO_ETHEREUM_TRANSACTION_HASH = (
    "0x89eaad85993cf0e77797bde24e133daddcc535e3230761a1c6738a42da690214"
)
"""
The hash go-ethereum reported for the simplest possible simulated call.

A transfer of `0x3e8` from `SENDER` to `RECIPIENT`, with every
transaction field left to its default. Reproducing it requires the
defaults to be exactly right — the nonce read from state, the gas limit
taken from the block's remaining gas, and an unsigned EIP-1559 envelope
with `r`, `s` and `yParity` all zero.
"""

IDENTITY_PRECOMPILE = "0x0000000000000000000000000000000000000004"
IDENTITY_TARGET = "0x0000000000000000000000000000000000001234"


SYSTEM_CONTRACT_NAMES = (
    "BEACON_ROOTS_ADDRESS",
    "HISTORY_STORAGE_ADDRESS",
    "WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS",
    "CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS",
    "BUILDER_DEPOSIT_CONTRACT_ADDRESS",
    "BUILDER_EXIT_CONTRACT_ADDRESS",
)
"""
System contracts a simulated block invokes before and after its calls.

A real chain has them all deployed at genesis, and the specification
refuses a block whose system contract holds no code, so a pre-state
this small has to stand them up. `STOP` is enough: none of these tests
is about what the contracts return.
"""


def _state(fork: str = "cancun") -> State:
    """Return a pre-state with a funded sender and the system contracts."""
    state = State()
    set_account(
        state,
        Bytes20(bytes.fromhex(SENDER[2:])),
        Account(nonce=Uint(0), balance=U256(0x7D0), code_hash=EMPTY_CODE_HASH),
    )
    fork_module = resolve_simulate_fork(fork).hardfork.module("fork")
    stop = store_code(state, Bytes(b"\x00"))
    for name in SYSTEM_CONTRACT_NAMES:
        address = getattr(fork_module, name, None)
        if address is None:
            continue
        set_account(
            state,
            address,
            Account(nonce=Uint(1), balance=U256(0), code_hash=stop),
        )
    return state


def _base_block() -> BaseBlock:
    """Return the chain head the simulations start from."""
    return BaseBlock(
        number=Uint(0),
        timestamp=U256(0),
        gas_limit=Uint(GAS_LIMIT),
        base_fee_per_gas=Uint(7),
        excess_blob_gas=U64(0),
        block_hash=Hash32(b"\0" * 32),
    )


def _simulator(payload: Dict[str, Any], fork: str = "cancun") -> EthSimulate:
    """Build a simulator over the shared pre-state."""
    return EthSimulate(
        fork=resolve_simulate_fork(fork),
        chain_id=U64(1),
        state=_state(fork),
        base_block=_base_block(),
        payload=SimulatePayload.parse(payload),
    )


def _simulate(
    payload: Dict[str, Any], fork: str = "cancun"
) -> List[SimulatedBlock]:
    """Run one payload against the shared pre-state."""
    return _simulator(payload, fork).run()


def _transfer(sender: str = SENDER, to: str = RECIPIENT) -> Dict[str, Any]:
    """Return the payload for a single ordinary transfer."""
    return {
        "blockStateCalls": [
            {"calls": [{"from": sender, "to": to, "value": "0x3e8"}]}
        ]
    }


def test_synthetic_transaction_matches_go_ethereum() -> None:
    """Derive the transaction hash a client puts in the simulated block."""
    blocks = _simulate(_transfer())
    result = blocks[0].call_results[0]
    assert "0x" + result.transaction_hash.hex() == (
        GO_ETHEREUM_TRANSACTION_HASH
    )


def test_transfer_succeeds_and_charges_intrinsic_gas() -> None:
    """A bare transfer costs 21000 and returns nothing."""
    result = _simulate(_transfer())[0].call_results[0]
    assert result.status == 1
    assert int(result.gas_used) == 21000
    assert int(result.max_used_gas) == 21000
    assert bytes(result.return_data) == b""


def test_calls_chain_within_a_block() -> None:
    """
    The second call spends what the first one delivered.

    This is what separates `eth_simulateV1` from `eth_call`: the
    recipient starts with nothing, so the second transfer can only
    succeed if it sees the first one's effect.
    """
    blocks = _simulate(
        {
            "blockStateCalls": [
                {
                    "calls": [
                        {"from": SENDER, "to": RECIPIENT, "value": "0x3e8"},
                        {
                            "from": RECIPIENT,
                            "to": THIRD_PARTY,
                            "value": "0x3e8",
                        },
                    ]
                }
            ]
        }
    )
    assert [result.status for result in blocks[0].call_results] == [1, 1]


def test_skipped_block_numbers_are_filled_in() -> None:
    """Jumping to block five reports the four empty blocks in between."""
    blocks = _simulate(
        {"blockStateCalls": [{"blockOverrides": {"number": "0x5"}}]}
    )
    assert [int(block.header.number) for block in blocks] == [1, 2, 3, 4, 5]
    assert [int(block.header.timestamp) for block in blocks] == [
        12,
        24,
        36,
        48,
        60,
    ]
    for parent, child in zip(blocks, blocks[1:], strict=False):
        assert child.header.parent_hash == parent.block_hash


def test_the_first_block_descends_from_the_base_block() -> None:
    """
    The base block's hash is the first simulated block's parent.

    It also has to reach `BLOCKHASH`, which is why the ancestor list
    carries it rather than starting empty.
    """
    blocks = _simulate({"blockStateCalls": [{}]})
    assert blocks[0].header.parent_hash == _base_block().block_hash


def test_block_numbers_must_increase() -> None:
    """A block that does not advance the number is rejected as -38020."""
    with pytest.raises(SimulateError) as raised:
        _simulate(
            {
                "blockStateCalls": [
                    {"blockOverrides": {"number": "0x5"}},
                    {"blockOverrides": {"number": "0x3"}},
                ]
            }
        )
    assert raised.value.code == -38020


def test_block_timestamps_are_checked_after_defaults() -> None:
    """
    An overridden timestamp is compared against the filled-in sequence.

    Skipping to block five puts four filler blocks in between, each
    twelve seconds later, so a timestamp of 30 is behind the 60 they
    reached even though it is well ahead of the parent's 0.
    """
    with pytest.raises(SimulateError) as raised:
        _simulate(
            {
                "blockStateCalls": [
                    {"blockOverrides": {"number": "0x5", "time": "0x1e"}}
                ]
            }
        )
    assert raised.value.code == -38021


def test_base_fee_is_zero_without_validation() -> None:
    """Calls are free unless the caller asks for validation."""
    blocks = _simulate({"blockStateCalls": [{}]})
    assert int(blocks[0].header.base_fee_per_gas) == 0


def test_base_fee_follows_the_parent_with_validation() -> None:
    """
    With validation on, the base fee is the EIP-1559 one.

    An empty parent leaves the fee where it was, since the decrease is
    floored at zero for a base fee this small.
    """
    blocks = _simulate({"validation": True, "blockStateCalls": [{}]})
    assert int(blocks[0].header.base_fee_per_gas) == 7


def test_an_inadmissible_call_abandons_the_request() -> None:
    """
    A nonce the block would reject fails the whole request.

    `eth_simulateV1` does not report such a call as a failed entry in
    the `calls` array: the spec exception is translated into the code
    that names the rule it broke.
    """
    with pytest.raises(SimulateError) as raised:
        _simulate(
            {
                "blockStateCalls": [
                    {
                        "calls": [
                            {
                                "from": SENDER,
                                "to": RECIPIENT,
                                "nonce": "0x0",
                            },
                            {
                                "from": SENDER,
                                "to": RECIPIENT,
                                "nonce": "0x0",
                            },
                        ]
                    }
                ]
            }
        )
    assert raised.value.code == -38010


def test_a_contract_may_send() -> None:
    """
    A sender with code is admitted, which consensus would refuse.

    Asserting the sender waives the EOA rule along with the recovery,
    and `eth_simulateV1` needs both waived: the method takes `from` at
    its word and the notes permit a contract there.
    """
    payload = {
        "blockStateCalls": [
            {
                "stateOverrides": {
                    SENDER: {"code": "0x600060005260206000f3"},
                },
                "calls": [{"from": SENDER, "to": RECIPIENT, "value": "0x3e8"}],
            }
        ]
    }
    assert _simulate(payload)[0].call_results[0].status == 1


def test_state_override_replaces_storage_wholesale() -> None:
    """
    `state` drops the account's existing slots; `stateDiff` merges.

    The two forms are told apart by whether the slot the first block
    wrote survives the second block's full replacement.
    """
    payload = {
        "blockStateCalls": [
            {"stateOverrides": {RECIPIENT: {"stateDiff": {"0x2": "0x9"}}}},
            {"stateOverrides": {RECIPIENT: {"state": {"0x3": "0x1"}}}},
        ]
    }
    simulator = _simulator(payload)
    simulator.run()
    recipient = Bytes20(bytes.fromhex(RECIPIENT[2:]))
    assert simulator.state.get_storage(
        recipient, U256(2).to_be_bytes32()
    ) == U256(0)
    assert simulator.state.get_storage(
        recipient, U256(3).to_be_bytes32()
    ) == U256(1)


def test_state_diff_keeps_the_slots_it_does_not_name() -> None:
    """The merging form leaves an untouched slot where it was."""
    payload = {
        "blockStateCalls": [
            {"stateOverrides": {RECIPIENT: {"stateDiff": {"0x2": "0x9"}}}},
            {"stateOverrides": {RECIPIENT: {"stateDiff": {"0x3": "0x1"}}}},
        ]
    }
    simulator = _simulator(payload)
    simulator.run()
    recipient = Bytes20(bytes.fromhex(RECIPIENT[2:]))
    assert simulator.state.get_storage(
        recipient, U256(2).to_be_bytes32()
    ) == U256(9)


def test_a_precompile_answers_at_its_new_address() -> None:
    """
    `movePrecompileToAddress` reaches the interpreter's dispatch table.

    Identity returns its input, so a call that comes back with the
    calldata proves the precompile really moved rather than the target
    merely holding an empty account.
    """
    payload = {
        "blockStateCalls": [
            {
                "stateOverrides": {
                    IDENTITY_PRECOMPILE: {
                        "movePrecompileToAddress": IDENTITY_TARGET
                    }
                },
                "calls": [
                    {
                        "from": SENDER,
                        "to": IDENTITY_TARGET,
                        "input": "0x" + "11" * 32,
                    }
                ],
            }
        ]
    }
    result = _simulate(payload)[0].call_results[0]
    assert result.status == 1
    assert bytes(result.return_data) == b"\x11" * 32


def test_moving_a_precompile_does_not_leak_between_runs() -> None:
    """
    The relocation dies with the block it was built for.

    The spike mutated the fork's module-level mapping in place, so a
    later request saw a precompile that an earlier one had moved. The
    mapping now lives on the block environment, so a second simulation
    finds identity where it always was.
    """
    _simulate(
        {
            "blockStateCalls": [
                {
                    "stateOverrides": {
                        IDENTITY_PRECOMPILE: {
                            "movePrecompileToAddress": IDENTITY_TARGET
                        }
                    }
                }
            ]
        }
    )
    result = _simulate(
        {
            "blockStateCalls": [
                {
                    "calls": [
                        {
                            "from": SENDER,
                            "to": IDENTITY_PRECOMPILE,
                            "input": "0x" + "22" * 32,
                        }
                    ]
                }
            ]
        }
    )[0].call_results[0]
    assert bytes(result.return_data) == b"\x22" * 32


def test_moving_a_precompile_to_itself_is_rejected() -> None:
    """A self-move is -38022, per the notes if not per the client."""
    with pytest.raises(SimulateError) as raised:
        _simulate(
            {
                "blockStateCalls": [
                    {
                        "stateOverrides": {
                            IDENTITY_PRECOMPILE: {
                                "movePrecompileToAddress": IDENTITY_PRECOMPILE
                            }
                        }
                    }
                ]
            }
        )
    assert raised.value.code == -38022


def test_trace_transfers_reports_the_top_level_transfer() -> None:
    """Before Amsterdam the option synthesizes the caller's transfer."""
    payload = dict(_transfer(), traceTransfers=True)
    logs = _simulate(payload)[0].call_results[0].logs
    assert [bytes(log.address) for log in logs] == [
        bytes(TRANSFER_LOG_EMITTER)
    ]


def test_trace_transfers_is_a_no_op_from_amsterdam() -> None:
    """
    From Amsterdam the consensus log supersedes the synthetic one.

    EIP-7708 puts a `Transfer` log in the receipts for the same
    movement, so synthesizing another would report it twice under two
    different emitters.
    """
    payload = dict(_transfer(), traceTransfers=True)
    logs = _simulate(payload, fork="amsterdam")[0].call_results[0].logs
    emitters = {bytes(log.address) for log in logs}
    assert bytes(TRANSFER_LOG_EMITTER) not in emitters
    assert logs, "EIP-7708 should have logged the transfer itself"


def test_a_gas_price_synthesizes_a_legacy_transaction() -> None:
    """
    Naming `gasPrice` alone puts the call in a pre-1559 envelope.

    The type is read back off the block rather than off the request, so
    this also checks that the transaction the trie committed to is the
    one the response describes.
    """
    payload = {
        "returnFullTransactions": True,
        "blockStateCalls": [
            {"calls": [{"from": SENDER, "to": RECIPIENT, "gasPrice": "0x0"}]}
        ],
    }
    transaction = _simulator(payload).result()[0]["transactions"][0]
    assert transaction["type"] == "0x0"
    assert "yParity" not in transaction


def test_a_gas_price_with_an_access_list_synthesizes_type_one() -> None:
    """An access list raises a pre-1559 call to the 2930 envelope."""
    payload = {
        "returnFullTransactions": True,
        "blockStateCalls": [
            {
                "calls": [
                    {
                        "from": SENDER,
                        "to": RECIPIENT,
                        "gasPrice": "0x0",
                        "accessList": [
                            {"address": RECIPIENT, "storageKeys": ["0x1"]}
                        ],
                    }
                ]
            }
        ],
    }
    transaction = _simulator(payload).result()[0]["transactions"][0]
    assert transaction["type"] == "0x1"
    assert transaction["accessList"][0]["address"] == RECIPIENT


def test_an_unnamed_type_stays_fee_market() -> None:
    """The overwhelmingly common payload names nothing and gets 1559."""
    payload = dict(_transfer(), returnFullTransactions=True)
    assert _simulator(payload).result()[0]["transactions"][0]["type"] == "0x2"


def test_withdrawals_are_paid_and_reported() -> None:
    """
    A `blockOverrides` withdrawal credits its recipient.

    It also has to reach the withdrawals trie, since the root of that
    trie is in the header and therefore in the block hash.
    """
    payload = {
        "blockStateCalls": [
            {
                "blockOverrides": {
                    "withdrawals": [
                        {
                            "index": "0x0",
                            "validatorIndex": "0x1",
                            "address": THIRD_PARTY,
                            "amount": "0x2",
                        }
                    ]
                }
            }
        ]
    }
    simulator = _simulator(payload)
    blocks = simulator.run()
    third_party = Bytes20(bytes.fromhex(THIRD_PARTY[2:]))
    account = simulator.state.get_account_optional(third_party)
    assert account is not None
    # Withdrawals are denominated in gwei.
    assert int(account.balance) == 2 * 10**9
    assert len(blocks[0].withdrawals) == 1
