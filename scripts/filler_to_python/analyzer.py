"""Analyze a parsed filler model and produce codegen IR."""

from __future__ import annotations

import json
import logging
import re
import warnings
from pathlib import Path
from typing import Any

import yaml
from execution_testing.base_types import Address
from execution_testing.base_types import Hash as EHash
from execution_testing.cli.evm_bytes import process_evm_bytes_string
from execution_testing.exceptions import TransactionException
from execution_testing.forks import get_forks
from execution_testing.specs import StateStaticTest
from execution_testing.specs.static_state.common import Tag, TagDict
from execution_testing.specs.static_state.common.tags import (
    ContractTag,
    SenderKeyTag,
    SenderTag,
)
from execution_testing.specs.static_state.expect_section import (
    ForkSet,
)
from execution_testing.specs.static_state.general_transaction import (
    GeneralTransactionInFiller,
)
from execution_testing.test_types import (
    EOA,
    Alloc,
    compute_create_address,
    eoa_from_hash,
)
from execution_testing.vm import Op

from .ir import (
    AccessListEntryIR,
    AccountAssertionIR,
    AccountIR,
    EnvironmentIR,
    ExpectEntryIR,
    ImportsIR,
    IntermediateTestModel,
    ParameterCaseIR,
    SenderIR,
    TransactionIR,
)

try:
    from execution_testing.cli.pytest_commands.plugins.filler.static_filler import (  # noqa: E501
        NoIntResolver,
    )
except ImportError:
    import yaml as _yaml

    class NoIntResolver(_yaml.SafeLoader):  # type: ignore[no-redef]
        """Fallback NoIntResolver."""

        pass


logger = logging.getLogger(__name__)

MAX_BYTECODE_OP_SIZE = 24576
SLOW_CATEGORIES = {
    "stQuadraticComplexityTest",
    "stStaticCall",
    "stTimeConsuming",
}

# Ported tests (relative to ``tests/ported_static/``) that must keep
# hardcoded addresses. These do not converge under ``exact-no-stack``
# with dynamic addresses because of patterns the analyzer's heuristics
# cannot cover:
#
# - EIP-2929 warm/cold gas accounting that depends on which addresses
#   are warm at call time (baseline-specific layout).
# - CREATE2 collision semantics that depend on specific pre-state
#   addresses colliding with computed CREATE2 targets.
# - Keccak-derived storage keys (Solidity mappings) baked into the
#   pre-state on specific sender / contract addresses.
# - Structural transaction rejections sensitive to exact pre-state
#   collisions (empty-but-code, init-colliding-with-non-empty).
# - Edge cases where dynamic allocation randomly picks an address
#   with a leading zero byte, changing PUSH size.
# - Tag resolution mismatches (analyzer resolves <contract:0x…hint>
#   to a fresh deterministic address, but baseline used the hint).
#
# Treat this list as an allowlist of "we've accepted the divergence
# here; don't try to make it dynamic". See trace-divergences.md for
# the per-file rationale.
FORCE_HARDCODED_TESTS: set[str] = {
    # GAS_ONLY (29) — EIP-2929 warm/cold access cost differences
    "stCallCodes/test_callcode_dynamic_code.py",
    "stCallCodes/test_callcode_dynamic_code2_self_call.py",
    "stCallCreateCallCodeTest/test_call1024_pre_calls.py",
    "stCallCreateCallCodeTest/test_contract_creation_make_call_that_ask_more_gas_then_transaction_provided.py",  # noqa: E501
    "stCreate2/test_returndatacopy_following_create.py",
    "stCreateTest/test_create_collision_to_empty2.py",
    "stCreateTest/test_create_transaction_refund_ef.py",
    "stDelegatecallTestHomestead/test_call1024_pre_calls.py",
    "stDelegatecallTestHomestead/test_delegatecode_dynamic_code2_self_call.py",  # noqa: E501
    "stEIP150singleCodeGasPrices/test_eip2929_oog.py",
    "stEIP2930/test_manual_create.py",
    "stEIP3651_warmcoinbase/test_coinbase_warm_account_call_gas_fail.py",
    "stEIP3855_push0/test_push0.py",
    "stEIP3855_push0/test_push0_gas2.py",
    "stHomesteadSpecific/test_contract_creation_oo_gdont_leave_empty_contract_via_transaction.py",  # noqa: E501
    "stRandom/test_random_statetest282.py",
    "stRandom/test_random_statetest287.py",
    "stRandom/test_random_statetest384.py",
    "stRandom2/test_random_statetest401.py",
    "stRandom2/test_random_statetest508.py",
    "stRevertTest/test_cost_revert.py",
    "stRevertTest/test_revert_opcode_in_calls_on_non_empty_return_data.py",
    "stRevertTest/test_revert_opcode_multiple_sub_calls.py",
    "stRevertTest/test_revert_precompiled_touch_paris.py",
    "stStackTests/test_underflow_test.py",
    "stSystemOperationsTest/test_suicide_caller_addres_too_big_left.py",
    "vmBitwiseLogicOperation/test_byte.py",
    "vmIOandFlowOperations/test_jump_to_push.py",
    "vmIOandFlowOperations/test_jumpi.py",
    # EXECUTION_PATH_DIVERGED — remaining 8 (Categories B, C, D, E)
    "stCreate2/test_create2_suicide.py",
    "stCreate2/test_create2collision_code2.py",
    "stCreate2/test_create2collision_selfdestructed2.py",
    "stDelegatecallTestHomestead/test_delegatecall_in_initcode_to_existing_contract_oog.py",  # noqa: E501
    "stLogTests/test_log1_non_empty_mem.py",
    "stSystemOperationsTest/test_double_selfdestruct_touch_paris.py",
    "stWalletTest/test_multi_owned_change_requirement_to1.py",
    "stWalletTest/test_multi_owned_revoke_nothing.py",
    # EXECUTION_PATH_DIVERGED + GAS (5)
    "stCreate2/test_create2collision_code.py",
    "stCreate2/test_create2collision_nonce.py",
    "stCreate2/test_create2collision_selfdestructed.py",
    "stCreate2/test_create2collision_selfdestructed_revert.py",
    "stSStoreTest/test_sstore_gas_left.py",
    # OUTPUT_DIFFERS — remaining 2 (Categories F, H)
    "stEIP3651_warmcoinbase/test_coinbase_warm_account_call_gas.py",
    "stWalletTest/test_multi_owned_is_owner_true.py",
    # Precompile-as-EOA — tests fund precompile addresses as EOAs,
    # then check nonce after calling the precompile. Dynamic EOAs
    # land at different addresses than the precompile targets.
    # STRUCTURAL — CREATE collision / EIP-3607 rejection behaviour.
    # With dynamic addresses the collision doesn't happen, so the tx
    # runs instead of being rejected → traces appear where baseline
    # had none.
    "stCreateTest/test_transaction_collision_to_empty_but_code.py",
    "stCreateTest/test_transaction_collision_to_empty_but_nonce.py",
    "stEIP3607/test_init_colliding_with_non_empty_account.py",
    "stEIP3607/test_transaction_colliding_with_non_empty_account_calls.py",
    "stEIP3607/test_transaction_colliding_with_non_empty_account_calls_itself.py",
    "stEIP3607/test_transaction_colliding_with_non_empty_account_init_paris.py",
    "stEIP3607/test_transaction_colliding_with_non_empty_account_send_paris.py",
    # Remaining CI assertion failures — gas measurements, keccak storage,
    # collision semantics, address-in-code, precompile interactions, etc.
    # that are fundamentally incompatible with dynamic addresses.
    "stBadOpcode/test_measure_gas.py",
    "stBadOpcode/test_operation_diff_gas.py",
    "stCallCodes/test_callcode_in_initcode_to_existing_contract_with_value_transfer.py",
    "stCreate2/test_create2collision_balance.py",
    "stCreate2/test_revert_depth_create_address_collision.py",
    "stCreate2/test_revert_depth_create_address_collision_berlin.py",
    "stCreateTest/test_create_empty_contract_with_storage.py",
    "stCreateTest/test_transaction_collision_to_empty2.py",
    "stDelegatecallTestHomestead/test_delegatecall_in_initcode_to_existing_contract.py",
    "stEIP1153_transientStorage/test_trans_storage_ok.py",
    "stEIP158Specific/test_call_one_v_call_suicide2.py",
    "stInitCodeTest/test_out_of_gas_prefunded_contract_creation.py",
    "stNonZeroCallsTest/test_non_zero_value_call_to_one_storage_key_paris.py",
    "stNonZeroCallsTest/test_non_zero_value_callcode_to_one_storage_key_paris.py",
    "stNonZeroCallsTest/test_non_zero_value_delegatecall_to_one_storage_key_paris.py",
    "stNonZeroCallsTest/test_non_zero_value_suicide_to_empty_paris.py",
    "stNonZeroCallsTest/test_non_zero_value_suicide_to_non_non_zero_balance.py",
    "stNonZeroCallsTest/test_non_zero_value_suicide_to_one_storage_key_paris.py",
    "stNonZeroCallsTest/test_non_zero_value_transaction_cal_lwith_data_to_one_storage_key_paris.py",
    "stNonZeroCallsTest/test_non_zero_value_transaction_call_to_one_storage_key_paris.py",
    "stPreCompiledContracts2/test_call_ecrecover0.py",
    "stPreCompiledContracts2/test_call_ecrecover0_complete_return_value.py",
    "stPreCompiledContracts2/test_call_ecrecover0_gas3000.py",
    "stPreCompiledContracts2/test_call_ecrecover0_overlapping_input_output.py",
    "stPreCompiledContracts2/test_call_ecrecover_check_length.py",
    "stPreCompiledContracts2/test_call_ecrecover_v_prefixed0.py",
    "stPreCompiledContracts2/test_callcode_ecrecover0.py",
    "stPreCompiledContracts2/test_callcode_ecrecover0_complete_return_value.py",
    "stPreCompiledContracts2/test_callcode_ecrecover0_gas3000.py",
    "stPreCompiledContracts2/test_callcode_ecrecover0_overlapping_input_output.py",
    "stPreCompiledContracts2/test_callcode_ecrecover_v_prefixed0.py",
    "stRandom/test_random_statetest144.py",
    "stRandom2/test_random_statetest642.py",
    "stRandom2/test_random_statetest645.py",
    "stRandom2/test_random_statetest646.py",
    "stRevertTest/test_revert_depth_create_address_collision.py",
    "stRevertTest/test_revert_in_create_in_init_paris.py",
    "stRevertTest/test_revert_prefound.py",
    "stRevertTest/test_revert_prefound_empty_paris.py",
    "stSpecialTest/test_failed_create_reverts_deletion_paris.py",
    "stSystemOperationsTest/test_create_hash_collision.py",
    "stSystemOperationsTest/test_test_random_test.py",
    "stWalletTest/test_day_limit_construction.py",
    "stWalletTest/test_day_limit_construction_partial.py",
    "stWalletTest/test_day_limit_reset_spent_today.py",
    "stWalletTest/test_day_limit_set_daily_limit.py",
    "stWalletTest/test_day_limit_set_daily_limit_no_data.py",
    "stWalletTest/test_multi_owned_add_owner_add_myself.py",
    "stWalletTest/test_multi_owned_change_owner_from_not_owner.py",
    "stWalletTest/test_multi_owned_change_owner_no_argument.py",
    "stWalletTest/test_multi_owned_change_owner_to_is_owner.py",
    "stWalletTest/test_multi_owned_change_requirement_to0.py",
    "stWalletTest/test_multi_owned_change_requirement_to2.py",
    "stWalletTest/test_multi_owned_construction_correct.py",
    "stWalletTest/test_multi_owned_remove_owner_by_non_owner.py",
    "stWalletTest/test_multi_owned_remove_owner_my_self.py",
    "stWalletTest/test_multi_owned_remove_owner_owner_is_not_owner.py",
    "stWalletTest/test_wallet_change_requirement_remove_pending_transaction.py",
    "stWalletTest/test_wallet_construction.py",
    "stWalletTest/test_wallet_construction_oog.py",
    "stWalletTest/test_wallet_construction_partial.py",
    "stWalletTest/test_wallet_kill.py",
    "stWalletTest/test_wallet_kill_to_wallet.py",
    "stWalletTest/test_wallet_remove_owner_remove_pending_transaction.py",
    "stZeroCallsRevert/test_zero_value_call_to_one_storage_key_oog_revert_paris.py",
    "stZeroCallsRevert/test_zero_value_callcode_to_one_storage_key_oog_revert_paris.py",
    "stZeroCallsRevert/test_zero_value_delegatecall_to_one_storage_key_oog_revert_paris.py",
    "stZeroCallsRevert/test_zero_value_suicide_to_one_storage_key_oog_revert_paris.py",
    "stZeroCallsTest/test_zero_value_call_to_one_storage_key_paris.py",
    "stZeroCallsTest/test_zero_value_callcode_to_one_storage_key_paris.py",
    "stZeroCallsTest/test_zero_value_delegatecall_to_one_storage_key_paris.py",
    "stZeroCallsTest/test_zero_value_suicide_to_empty_paris.py",
    "stZeroCallsTest/test_zero_value_suicide_to_non_zero_balance.py",
    "stZeroCallsTest/test_zero_value_suicide_to_one_storage_key_paris.py",
    "stZeroCallsTest/test_zero_value_transaction_cal_lwith_data_to_one_storage_key_paris.py",
    "stZeroCallsTest/test_zero_value_transaction_call_to_one_storage_key_paris.py",
    # Slow-marked tests that fail with dynamic addresses (excluded from
    # the main verification by -m "not slow" but exercised on full CI
    # runs without that filter — same KV_CALL_FLIP / collision /
    # ecrecover patterns as the non-slow allowlisted siblings).
    "stQuadraticComplexityTest/test_return50000.py",
    "stQuadraticComplexityTest/test_return50000_2.py",
    "stStaticCall/test_static_call_ecrecover0.py",
    "stStaticCall/test_static_call_ecrecover0_complete_return_value.py",
    "stStaticCall/test_static_call_ecrecover0_gas3000.py",
    "stStaticCall/test_static_call_ecrecover0_overlapping_input_output.py",
    "stStaticCall/test_static_call_ecrecover_check_length.py",
    "stStaticCall/test_static_call_ecrecover_v_prefixed0.py",
    "stStaticCall/test_static_call_to_call_code_op_code_check.py",
    "stStaticCall/test_static_call_to_call_op_code_check.py",
    "stStaticCall/test_static_call_to_del_call_op_code_check.py",
    "stStaticCall/test_static_call_to_static_op_code_check.py",
    "stStaticCall/test_static_check_opcodes.py",
    "stStaticCall/test_static_check_opcodes2.py",
    "stStaticCall/test_static_check_opcodes3.py",
    "stStaticCall/test_static_check_opcodes4.py",
    "stStaticCall/test_static_check_opcodes5.py",
}


def _ported_rel_path(filler_path: Path) -> str:
    """Return the ``<category>/test_<snake>.py`` path for a filler."""
    category = filler_path.parent.name if filler_path.parent.name else ""
    py_test_name = _filler_name_to_test_name(filler_path.stem)
    return f"{category}/{py_test_name}.py"


class _AnalyzerAlloc(Alloc):
    """Alloc subclass that supports fund_eoa for analysis."""

    _eoa_counter: int = 0

    def fund_eoa(
        self,
        _amount: Any = None,
        _label: Any = None,
        **_kwargs: Any,
    ) -> EOA:
        """Create a deterministic EOA for analysis."""
        self._eoa_counter += 1
        h = EHash(self._eoa_counter.to_bytes(32, "big"))
        return eoa_from_hash(h, 0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_filler(path: Path) -> tuple[str, StateStaticTest]:
    """Load a filler file and return (test_name, validated model)."""
    with open(path) as f:
        if path.suffix == ".json":
            data = json.load(f)
        else:
            data = yaml.load(f, Loader=NoIntResolver)

    test_name = next(iter(data))
    model = StateStaticTest.model_validate(data[test_name])
    model.test_name = test_name
    return test_name, model


def analyze(
    test_name: str,
    model: StateStaticTest,
    filler_path: Path,
) -> IntermediateTestModel:
    """Analyze a parsed filler model and produce codegen IR."""
    # 1. Gather all tag dependencies
    all_deps: dict[str, Tag] = {}
    all_deps.update(model.transaction.tag_dependencies())
    for expect in model.expect:
        all_deps.update(expect.result.tag_dependencies())
    imports = ImportsIR()

    # 2. Resolve tags via pre-state setup
    pre = _AnalyzerAlloc()
    tags = model.pre.setup(pre, all_deps)

    # 2b. Honour precompile hint addresses for tagged EOAs.
    # The static filler resolves ``<eoa:0x...01>`` through
    # ``eoa_from_hash`` (random placeholder address). LLL source code
    # however references those addresses literally (e.g.
    # ``(call gas 0x01 ...)``), so the bytecode lands at the precompile
    # while the funded EOA lands somewhere else. Override the resolved
    # address back to the literal hint when it falls in the precompile
    # range (0x01-0x10) — that way ``addr_to_var`` registers 0x01 and
    # tx-data / post-state resolutions stay consistent with bytecode.
    #
    # Track the override addresses so that the corresponding EOA can
    # be pinned non-dynamic later. Without pinning, the variable in
    # the generated test (``addr_5``) would still go through
    # ``pre.fund_eoa()`` at runtime and land at a random address,
    # while ``tx_data`` would carry that random address — breaking
    # any contract that calls the literal precompile (0x01).
    pinned_eoa_addrs: set[Address] = set()
    for tag in model.pre.root.keys():
        if not isinstance(tag, SenderTag):
            continue
        name = tag.name
        if not (
            isinstance(name, str) and name.startswith("0x") and len(name) == 42
        ):
            continue
        try:
            hint_int = int(name, 16)
        except ValueError:
            continue
        if 1 <= hint_int <= 0x10:
            hint_addr = Address(hint_int)
            tags[tag.name] = hint_addr
            pinned_eoa_addrs.add(hint_addr)

    # 3. Fork range (must sort chronologically, not alphabetically)
    all_fork_names = [str(f) for f in sorted(get_forks())]
    valid_forks_set = set(model.get_valid_at_forks())
    valid_forks_chrono = [f for f in all_fork_names if f in valid_forks_set]
    valid_from = valid_forks_chrono[0] if valid_forks_chrono else "Cancun"

    valid_until: str | None = None
    if valid_forks_chrono and valid_forks_chrono[-1] != all_fork_names[-1]:
        valid_until = valid_forks_chrono[-1]

    # 4. Category from filler path
    category = filler_path.parent.name if filler_path.parent.name else ""

    # 5. Build address -> variable name mapping
    addr_to_var = _assign_variable_names(model, tags)

    # 5b. Resolve coinbase address for later use
    coinbase_addr: Address | None = None
    if isinstance(model.env.current_coinbase, Tag):
        tag_name = model.env.current_coinbase.name
        if tag_name in tags:
            resolved = tags[tag_name]
            if isinstance(resolved, Address):
                coinbase_addr = resolved
            else:
                coinbase_addr = Address(int.from_bytes(resolved, "big"))
    else:
        coinbase_addr = model.env.current_coinbase

    # 6. Identify sender
    sender_ir, sender_tag_name = _build_sender_ir(model, tags)

    # 7. Build TX arrays
    probably_bytecode = model.transaction.to is None
    tx_data, tx_gas, tx_value = _build_tx_arrays(
        model.transaction,
        tags,
        addr_to_var,
        probably_bytecode,
        imports,
    )

    # 8. Parameter matrix
    parameters = _build_parameters(model)
    is_multi_case = len(parameters) > 1

    # Detect fork-dependent single-case tests (multiple expect sections
    # with different networks but only one (d, g, v) combo)
    is_fork_dependent = not is_multi_case and len(model.expect) > 1

    # 9. Build accounts
    force_hardcoded = _ported_rel_path(filler_path) in FORCE_HARDCODED_TESTS
    accounts = _build_accounts(
        model,
        tags,
        addr_to_var,
        sender_tag_name,
        imports,
        force_hardcoded=force_hardcoded,
        coinbase_addr=coinbase_addr,
        pinned_eoa_addrs=pinned_eoa_addrs,
    )

    # Track if sender is not in the pre-state (for fund_eoa handling).
    # When True, the generated test uses pre.fund_eoa(amount=0) instead
    # of EOA(key=...), matching the static fill's setup() step 7.
    if sender_tag_name and not any(a.is_sender for a in accounts):
        sender_ir.not_in_pre = True

    # 10. Build environment
    environment_ir = _build_environment(model, tags, addr_to_var)

    # 11. Build expect entries
    expect_entries = _build_expect_entries(
        model, tags, addr_to_var, all_fork_names, imports
    )

    # 11b. If post-state has unresolvable addresses — either as account
    # references (Address(0x...)) or as address-like storage values
    # (large ints > 2^32 that weren't resolved to variable names) —
    # disable dynamic for ALL accounts (including sender) so every
    # address stays fixed and CREATE-derived addresses match baseline.
    # Values above 2**32 are likely addresses, not small ints.
    addr_like_threshold = 0x100000000
    has_unresolved = any(
        "Address(0x" in a.var_ref
        for entry in expect_entries
        for a in entry.result
    ) or any(
        isinstance(v, int) and v >= addr_like_threshold
        for entry in expect_entries
        for a in entry.result
        if a.storage is not None
        for v in a.storage.values()
    )
    if has_unresolved:
        for acct in accounts:
            acct.use_dynamic = False

    # Sender: dynamic unless unresolvable post-state or hardcoded allowlist.
    sender_ir.use_dynamic = not force_hardcoded and not has_unresolved

    # 11c. Forced hardcoded (allowlist) also pins every EOA so coinbase
    # rebinds and fund_eoa-generated EOAs don't leak into an otherwise
    # hardcoded test.
    if force_hardcoded:
        for acct in accounts:
            acct.use_dynamic = False

    # 12. Build transaction IR
    transaction_ir, access_list_entries = _build_transaction_ir(
        model,
        tags,
        addr_to_var,
        tx_data,
        tx_gas,
        tx_value,
        is_multi_case,
        imports,
    )

    # 13. Address constants (non-tagged, non-sender addresses)
    address_constants = _build_address_constants(
        model, tags, addr_to_var, sender_tag_name, accounts
    )

    # 14. Import flags
    if access_list_entries or any(
        model.transaction.data[d.index].access_list is not None
        for d in model.transaction.data
    ):
        imports.needs_access_list = True

    if (
        imports.needs_access_list
        or model.transaction.blob_versioned_hashes is not None
    ):
        imports.needs_hash = True

    if any(p.has_exception for p in parameters):
        imports.needs_tx_exception = True

    # 15. Filler comment
    filler_comment = ""
    if model.info and model.info.comment:
        filler_comment = model.info.comment

    # 16. Test name
    py_test_name = _filler_name_to_test_name(test_name)

    # 17. Whether the test mutates the pre-allocation. The framework's
    # ``assert_mutable()`` is triggered by:
    #   * ``pre[var] = Account(...)``       (any non-dynamic account)
    #   * ``EOA(key=...)``                  (non-dynamic sender)
    #   * ``pre.deploy_contract(address=...)``  (non-dynamic contract)
    #   * ``pre.deploy_contract(..., nonce=0)`` (default emit when the
    #     filler's account had nonce 0 or unset)
    #   * ``pre.fund_eoa(nonce=...)``       (dynamic sender with explicit
    #     nonce — used for high-nonce senders)
    # Tests not hitting any of these can run under the ``execute`` plugin.
    # The template only emits ``pre.fund_eoa(nonce=...)`` when
    # ``sender.nonce`` is truthy, and ``pre.deploy_contract(..., nonce=N)``
    # always emits N (defaulting to 0 when ``account.nonce`` is None).
    # Mirror those conditions exactly.
    sender_emits_nonce_kwarg = bool(sender_ir.nonce)
    contract_nonce_zero = any(
        not a.is_eoa and (a.nonce is None or a.nonce == 0) for a in accounts
    )
    needs_mutable_pre = (
        not sender_ir.use_dynamic
        or sender_emits_nonce_kwarg
        or any(not a.use_dynamic for a in accounts)
        or contract_nonce_zero
    )

    return IntermediateTestModel(
        test_name=py_test_name,
        filler_path=str(filler_path),
        filler_comment=filler_comment,
        category=category,
        valid_from=valid_from,
        valid_until=valid_until,
        is_slow=(
            (model.info is not None and "slow" in model.info.pytest_marks)
            or category in SLOW_CATEGORIES
        ),
        is_multi_case=is_multi_case,
        is_fork_dependent=is_fork_dependent,
        needs_mutable_pre=needs_mutable_pre,
        environment=environment_ir,
        accounts=accounts,
        sender=sender_ir,
        parameters=parameters,
        transaction=transaction_ir,
        expect_entries=expect_entries,
        address_constants=address_constants,
        tx_data=tx_data,
        tx_gas=tx_gas,
        tx_value=tx_value,
        imports=imports,
    )


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    return s.lower()


def _filler_name_to_test_name(filler_stem: str) -> str:
    """Convert filler stem to Python test function name."""
    name = re.sub(r"Filler$", "", filler_stem)
    result = "test_" + _camel_to_snake(name)
    result = result.replace("+", "_plus_")
    result = result.replace("-", "_minus_")
    result = re.sub(r"[^a-z0-9_]", "_", result)
    result = re.sub(r"_+", "_", result)
    return result.strip("_")


def _classify_code_source(source: str) -> str:
    """Classify code source and format as a comment block."""
    if not source or source.strip() == "":
        return ""

    stripped = source.strip()

    if stripped.startswith(":yul"):
        lang = "yul"
        body = stripped[4:].strip()
    elif stripped.startswith("{") or stripped.startswith("(asm"):
        lang = "lll"
        body = stripped
    elif stripped.startswith(":abi"):
        lang = "abi"
        body = stripped[4:].strip()
    elif stripped.startswith(":raw"):
        lang = "raw"
        body = stripped[4:].strip()
    elif stripped.startswith("0x"):
        lang = "hex"
        body = stripped
    else:
        lang = "unknown"
        body = stripped

    lines = body.split("\n")
    if len(lines) > 30:
        lines = lines[:30] + [f"... ({len(lines) - 30} more lines)"]

    comment_lines = [f"    # Source: {lang}"]
    for line in lines:
        comment_lines.append(f"    # {line}")
    return "\n".join(comment_lines)


def _get_int_definitions(
    addr_to_var: dict[Address | EOA, str] | None,
) -> dict[int, str]:
    """
    Convert variable dictionary to int definitions used by the evm bytecode
    parser.
    """
    result: dict[int, str] = {}
    if not addr_to_var:
        return result
    for k, v in addr_to_var.items():
        result[int.from_bytes(k, "big")] = v
    return result


def _bytes_to_op_expr(
    code_bytes: bytes,
    addr_to_var: dict[Address | EOA, str] | None = None,
) -> str | None:
    """Convert compiled bytecode to Op expression string."""
    if not code_bytes or len(code_bytes) > MAX_BYTECODE_OP_SIZE:
        return None

    hex_str = code_bytes.hex()
    if not hex_str:
        return None

    try:
        int_definitions = _get_int_definitions(addr_to_var)
        op_str = process_evm_bytes_string(
            hex_str,
            assembly=False,
            int_definitions=int_definitions,
        )
        # Roundtrip check
        compiled = eval(
            op_str, {"Op": Op}, {v: k for k, v in int_definitions.items()}
        )  # noqa: S307
        if compiled.hex() != hex_str.lower():
            return None
        return op_str
    except Exception:
        return None


def _assign_variable_names(
    model: StateStaticTest, tags: TagDict
) -> dict[Address | EOA, str]:
    """Build address -> variable name mapping."""
    addr_to_var: dict[Address | EOA, str] = {}
    contract_counter = 0

    # Coinbase
    coinbase_addr: Address | None = None
    if isinstance(model.env.current_coinbase, Tag):
        tag_name = model.env.current_coinbase.name
        if tag_name in tags:
            coinbase_addr = tags[tag_name]
    else:
        coinbase_addr = model.env.current_coinbase

    if coinbase_addr:
        addr_to_var[coinbase_addr] = "coinbase"

    # Sender
    sender_addr: Address | EOA | None = None
    if isinstance(model.transaction.secret_key, SenderKeyTag):
        tag_name = model.transaction.secret_key.name
        if tag_name in tags:
            sender_addr = tags[tag_name]
    else:
        # Non-tagged sender: derive address from key
        sender_addr = EOA(key=model.transaction.secret_key)

    if sender_addr:
        addr_to_var[sender_addr] = "sender"

    # Tagged pre-state accounts
    for address_or_tag, _account in model.pre.root.items():
        if isinstance(address_or_tag, Tag):
            tag_name = address_or_tag.name
            if tag_name in tags:
                addr = tags[tag_name]
                if addr not in addr_to_var:
                    var_name = _sanitize_var_name(
                        tag_name, set(addr_to_var.values())
                    )
                    addr_to_var[addr] = var_name

    # Non-tagged pre-state accounts
    for address_or_tag, _account in model.pre.root.items():
        if not isinstance(address_or_tag, Tag):
            if address_or_tag not in addr_to_var:
                var_name = f"contract_{contract_counter}"
                contract_counter += 1
                addr_to_var[address_or_tag] = var_name

    # Transaction "to" address
    if model.transaction.to is not None:
        if isinstance(model.transaction.to, Tag):
            tag_name = model.transaction.to.name
            if tag_name in tags:
                to_addr = tags[tag_name]
                if to_addr not in addr_to_var:
                    var_name = _sanitize_var_name(
                        tag_name, set(addr_to_var.values())
                    )
                    addr_to_var[to_addr] = var_name

    return addr_to_var


def _sanitize_var_name(name: str, used: set[str]) -> str:
    """Sanitize a tag name into a valid Python variable name."""
    var = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    var = re.sub(r"_+", "_", var).strip("_").lower()
    if re.match(r"0x[0-9a-f]{40}", var):
        # Some tagged tests use addresses as tags, which is confusing, remove
        var = "addr"
    if not var or var[0].isdigit():
        var = "addr_" + var
    # Avoid Python keywords and builtins
    _reserved = {
        "type",
        "hash",
        "id",
        "input",
        "range",
        "list",
        "dict",
        "return",
        "class",
        "def",
        "for",
        "if",
        "else",
        "elif",
        "while",
        "break",
        "continue",
        "pass",
        "import",
        "from",
        "as",
        "with",
        "try",
        "except",
        "finally",
        "raise",
        "yield",
        "lambda",
        "global",
        "nonlocal",
        "assert",
        "del",
        "in",
        "is",
        "not",
        "and",
        "or",
        "True",
        "False",
        "None",
        "async",
        "await",
        "print",
        "exec",
        "eval",
        "open",
        "map",
        "filter",
        "set",
        "bytes",
        "int",
        "str",
        "float",
        "bool",
        "object",
        "super",
        "property",
        "staticmethod",
        "classmethod",
        "abs",
        "all",
        "any",
        "bin",
        "hex",
        "oct",
        "len",
        "max",
        "min",
        "pow",
        "sum",
        "zip",
    }
    if var in _reserved:
        var = var + "_"
    base = var
    counter = 2
    while var in used:
        var = f"{base}_{counter}"
        counter += 1
    return var


def _addr_hex(addr: Address | EOA) -> str:
    """Normalize an address-like value to hex string."""
    hex_str = str(addr)[2:].lstrip("0")
    if hex_str == "":
        hex_str = "0"
    return f"0x{hex_str}"


def _build_sender_ir(
    model: StateStaticTest, tags: TagDict
) -> tuple[SenderIR, str | None]:
    """Build SenderIR and return (sender_ir, sender_tag_name)."""
    if isinstance(model.transaction.secret_key, SenderKeyTag):
        tag_name = model.transaction.secret_key.name
        # Get the filler-derived key from tags (eoa_from_hash result)
        resolved = tags.get(tag_name)
        if isinstance(resolved, EOA):
            key = resolved.key
            assert key is not None
            key_int = int.from_bytes(key, "big")
        else:
            key_int = 0
        # Find sender balance and nonce from pre-state
        balance = 0
        nonce: int | None = None
        for address_or_tag, account in model.pre.root.items():
            if isinstance(address_or_tag, SenderTag):
                if address_or_tag.name == tag_name:
                    balance = int(account.balance) if account.balance else 0
                    if account.nonce is not None:
                        nonce = int(account.nonce)
                    break
        return (
            SenderIR(
                is_tagged=False, key=key_int, balance=balance, nonce=nonce
            ),
            tag_name,
        )
    else:
        # Find sender balance and nonce from pre-state
        eoa = EOA(key=model.transaction.secret_key)
        sender_addr = _addr_hex(eoa)
        balance = 0
        nonce = None
        for address_or_tag, account in model.pre.root.items():
            if not isinstance(address_or_tag, Tag):
                if _addr_hex(address_or_tag) == sender_addr:
                    balance = int(account.balance) if account.balance else 0
                    if account.nonce is not None:
                        nonce = int(account.nonce)
                    break
        return SenderIR(
            is_tagged=False,
            key=int.from_bytes(eoa.key, "big"),
            balance=balance,
            nonce=nonce,
        ), None


def _build_parameters(model: StateStaticTest) -> list[ParameterCaseIR]:
    """Build the (d, g, v) parameter matrix."""
    parameters: list[ParameterCaseIR] = []
    for d in model.transaction.data:
        for g in range(len(model.transaction.gas_limit)):
            for v in range(len(model.transaction.value)):
                has_exc = False
                for expect in model.expect:
                    if (
                        expect.has_index(d.index, g, v)
                        and expect.expect_exception is not None
                    ):
                        has_exc = True

                # Build ID label (same logic as fill_function)
                id_label = ""
                if len(model.transaction.data) > 1 or d.label is not None:
                    if d.label is not None:
                        id_label = f"{d}"
                    else:
                        id_label = f"d{d}"
                if len(model.transaction.gas_limit) > 1:
                    id_label += f"-g{g}"
                if len(model.transaction.value) > 1:
                    id_label += f"-v{v}"

                marks = "pytest.mark.exception_test" if has_exc else None

                parameters.append(
                    ParameterCaseIR(
                        d=d.index,
                        g=g,
                        v=v,
                        has_exception=has_exc,
                        label=d.label,
                        id=id_label,
                        marks=marks,
                    )
                )
    return parameters


def _resolve_storage_values(
    storage: dict[int, int],
    addr_to_var: dict[Address | EOA, str],
    imports: ImportsIR | None = None,
) -> dict[int, int | str]:
    """Replace storage values matching known addresses with var names."""
    if not storage or not addr_to_var:
        return storage
    # Build int -> var_name lookup from addr_to_var
    int_to_var: dict[int, str] = {}
    for addr, var_name in addr_to_var.items():
        int_to_var[int.from_bytes(addr, "big")] = var_name
    # Also build CREATE-derived address lookup
    create_to_expr: dict[int, str] = {}
    for addr, var_name in addr_to_var.items():
        for nonce in range(256):
            created = compute_create_address(address=addr, nonce=nonce)
            created_int = int.from_bytes(created, "big")
            if created_int not in int_to_var:
                create_to_expr[created_int] = (
                    f"compute_create_address(address={var_name},"
                    f" nonce={nonce})"
                )
    result: dict[int, int | str] = {}
    for k, v in storage.items():
        if v in int_to_var:
            result[k] = int_to_var[v]
        elif v in create_to_expr:
            if imports is not None:
                imports.needs_compute_create_address = True
            result[k] = create_to_expr[v]
        else:
            result[k] = v
    return result


def _find_address_refs_in_bytecode(
    code_bytes: bytes,
    known_addresses: set[Address],
) -> dict[Address, int]:
    """
    Find known addresses referenced in bytecode via PUSH.

    Return a mapping ``address -> minimum PUSH size observed``.
    A push size < 20 means the baseline bytecode compiled the
    address to fewer bytes (leading zero bytes); the referenced
    contract must stay hardcoded so the compiler keeps emitting
    the same short PUSH opcode and the trace stays aligned.
    """
    refs: dict[Address, int] = {}
    # Pre-compute int values for fast comparison
    known_ints = {int.from_bytes(a, "big") for a in known_addresses}
    i = 0
    while i < len(code_bytes):
        opcode = code_bytes[i]
        if 0x60 <= opcode <= 0x7F:  # PUSH1..PUSH32
            push_size = opcode - 0x5F
            push_data = code_bytes[i + 1 : i + 1 + push_size]
            if len(push_data) == push_size:
                # Addresses with leading zero bytes are compiled to
                # a PUSH smaller than PUSH20 (down to PUSH1 for 1-byte
                # addresses like 0x01). Match on int value against the
                # known-address set — false positives would require a
                # PUSHn that happens to push exactly a value already
                # registered as a pre-state address, which is rare in
                # practice.
                val = int.from_bytes(push_data, "big")
                if val in known_ints:
                    addr = Address(val)
                    if addr not in refs or push_size < refs[addr]:
                        refs[addr] = push_size
            i += 1 + push_size
        else:
            i += 1
    return refs


def _topological_sort_contracts(
    contract_addrs: list[Address],
    deps: dict[Address, set[Address]],
) -> tuple[list[Address], set[Address]]:
    """
    Return (sorted_addresses, cycle_addresses).

    If A's bytecode references B, B must be deployed before A.
    """
    addr_set = set(contract_addrs)
    # forward[B] = {A} means A depends on B, so B must come first
    forward: dict[Address, set[Address]] = {a: set() for a in addr_set}  # noqa: C420
    in_deg: dict[Address, int] = dict.fromkeys(addr_set, 0)
    for a, dep_set in deps.items():
        if a not in addr_set:
            continue
        for b in dep_set:
            if b in addr_set:
                forward[b].add(a)
                in_deg[a] += 1

    # Kahn's algorithm
    queue = [a for a in contract_addrs if in_deg[a] == 0]
    sorted_addrs: list[Address] = []
    while queue:
        node = queue.pop(0)
        sorted_addrs.append(node)
        for neighbor in forward[node]:
            in_deg[neighbor] -= 1
            if in_deg[neighbor] == 0:
                queue.append(neighbor)

    cycle_addrs = addr_set - set(sorted_addrs)
    return sorted_addrs, cycle_addrs


def _build_accounts(
    model: StateStaticTest,
    tags: TagDict,
    addr_to_var: dict[Address | EOA, str],
    sender_tag_name: str | None,
    imports: ImportsIR,
    *,
    force_hardcoded: bool = False,
    coinbase_addr: Address | None = None,
    pinned_eoa_addrs: set[Address] | None = None,
) -> list[AccountIR]:
    """Build AccountIR list with dependency-ordered contracts."""
    if pinned_eoa_addrs is None:
        pinned_eoa_addrs = set()
    # ------------------------------------------------------------------
    # Pass 1: gather account metadata and compile bytecode (no Op yet)
    # ------------------------------------------------------------------
    raw_accounts: list[AccountIR] = []
    # Map address -> compiled code_bytes for contracts (for dep analysis)
    code_bytes_map: dict[Address, bytes] = {}

    for address_or_tag, account in model.pre.root.items():
        is_tagged = isinstance(address_or_tag, Tag)
        # SenderTag type is always EOA, ContractTag is always contract
        is_eoa = isinstance(address_or_tag, SenderTag) if is_tagged else False
        is_sender = False

        if is_tagged:
            tag_name = address_or_tag.name
            if sender_tag_name and tag_name == sender_tag_name:
                is_sender = True
                is_eoa = True
            resolved = tags.get(tag_name)
            var_name = (
                addr_to_var.get(resolved, tag_name)
                if resolved is not None
                else tag_name
            )
            address = resolved
        else:
            address_str = str(address_or_tag)
            var_name = addr_to_var.get(
                address_or_tag, f"addr_{address_str[:10]}"
            )
            # Check if this non-tagged address is the sender
            if addr_to_var.get(address_or_tag) == "sender":
                is_sender = True
                is_eoa = True
            address = address_or_tag

        assert not var_name.startswith("0x")

        # Determine if non-tagged account has code (is a contract)
        has_code = account.code is not None and account.code.source.strip()
        if not is_tagged and not is_eoa and not has_code:
            # Non-tagged, no code — treat as EOA
            is_eoa = True

        # Compile code but defer Op expression conversion
        source_comment = ""
        code_bytes: bytes = b""
        oversized_code = False
        if has_code:
            source_comment = _classify_code_source(account.code.source)
            try:
                code_bytes = account.code.compiled(tags)
                if len(code_bytes) > MAX_BYTECODE_OP_SIZE:
                    oversized_code = True
            except Exception as e:
                warnings.warn(
                    f"Code compilation failed for {var_name}: {e}",
                    stacklevel=2,
                )

        # Storage
        storage: dict[int, int | str] = {}
        if account.storage and account.storage.root:
            resolved_storage = account.storage.resolve(tags)
            for k, v in resolved_storage.items():
                storage[int(k)] = int(v)
            storage = _resolve_storage_values(storage, addr_to_var, imports)

        # Balance and nonce
        balance = int(account.balance) if account.balance is not None else 0
        nonce = int(account.nonce) if account.nonce is not None else None

        acct_ir = AccountIR(
            var_name=var_name,
            is_tagged=is_tagged,
            is_eoa=is_eoa,
            is_sender=is_sender,
            balance=balance,
            nonce=nonce,
            address=address,
            source_comment=source_comment,
            code_expr="",
            storage=storage,
            oversized_code=oversized_code,
            use_dynamic=True,
        )

        # Oversized contracts must keep hardcoded address
        if oversized_code:
            acct_ir.use_dynamic = False

        # Coinbase account must keep hardcoded address so
        # Environment(fee_recipient=coinbase) and the pre-state
        # entry refer to the same address.
        if (
            coinbase_addr is not None
            and address is not None
            and int.from_bytes(address, "big")
            == int.from_bytes(coinbase_addr, "big")
        ):
            acct_ir.use_dynamic = False

        raw_accounts.append(acct_ir)
        if code_bytes and address is not None:
            code_bytes_map[address] = code_bytes

    # ------------------------------------------------------------------
    # Build dependency graph and topological sort for contracts
    # ------------------------------------------------------------------
    known_contract_addrs: set[Address] = set()
    for acct in raw_accounts:
        if not acct.is_eoa and acct.address is not None:
            known_contract_addrs.add(acct.address)

    # All known addresses (contracts + EOAs) for bytecode ref scanning
    all_known_addrs: set[Address] = set()
    for addr_or_eoa in addr_to_var:
        if isinstance(addr_or_eoa, Address):
            all_known_addrs.add(addr_or_eoa)
        else:
            all_known_addrs.add(Address(int.from_bytes(addr_or_eoa, "big")))

    # Pre-state EOA addresses — used to recognise short-PUSH refs that
    # point at funded EOAs (e.g. precompile addresses 0x01-0x10 listed
    # as ``<eoa:0x...01>`` in the filler) instead of contracts.
    known_eoa_addrs: set[Address] = set()
    for acct in raw_accounts:
        if acct.is_eoa and acct.address is not None:
            known_eoa_addrs.add(acct.address)

    deps: dict[Address, set[Address]] = {}
    # Contract addresses referenced via PUSH<20 anywhere: baseline
    # bytecode compiled them to a short PUSH because of leading zero
    # bytes, so they must stay hardcoded to keep the opcode sequence
    # aligned.
    short_push_refs: set[Address] = set()
    # EOA addresses referenced via PUSH<20 — pin those EOAs to their
    # literal address so the funded account lands at the precompile
    # (e.g. 0x01) instead of a random ``pre.fund_eoa`` address.
    short_push_eoa_refs: set[Address] = set()
    # True when a short-PUSH ref targets an address that is neither a
    # pre-state contract nor a pre-state EOA (e.g. an external tag
    # like <contract:0x...dead> only referenced from bytecode). No
    # account can be pinned, so fall back to globally disabling
    # dynamic addresses for the whole test.
    short_push_unpinnable = False
    for addr, cb in code_bytes_map.items():
        refs = _find_address_refs_in_bytecode(cb, all_known_addrs)
        # Track deps on other contracts. Keep self-references — they
        # create self-loops detected as cycles, forcing hardcoded addr.
        deps[addr] = set(refs) & known_contract_addrs
        for ref_addr, push_size in refs.items():
            if push_size < 20:
                if ref_addr in known_contract_addrs:
                    short_push_refs.add(ref_addr)
                elif ref_addr in known_eoa_addrs:
                    short_push_eoa_refs.add(ref_addr)
                else:
                    short_push_unpinnable = True

    contract_addrs_ordered = [
        acct.address
        for acct in raw_accounts
        if not acct.is_eoa and acct.address is not None
    ]
    sorted_addrs, cycle_addrs = _topological_sort_contracts(
        contract_addrs_ordered, deps
    )

    # Mark cycle contracts as non-dynamic, then propagate: any contract
    # referenced by a non-dynamic contract must also be non-dynamic
    # (because the non-dynamic bytecode contains the old address).
    non_dynamic_addrs = set(cycle_addrs)
    for acct in raw_accounts:
        if acct.oversized_code and acct.address is not None:
            non_dynamic_addrs.add(acct.address)
    # Short-PUSH refs: pin the referenced contract so its address keeps
    # the same leading-zero profile as baseline.
    non_dynamic_addrs.update(short_push_refs)

    changed = True
    while changed:
        changed = False
        for addr in list(non_dynamic_addrs):
            for ref in deps.get(addr, set()):
                if (
                    ref not in non_dynamic_addrs
                    and ref in known_contract_addrs
                ):
                    non_dynamic_addrs.add(ref)
                    changed = True

    for acct in raw_accounts:
        if acct.address in non_dynamic_addrs:
            acct.use_dynamic = False

    # Pin EOAs whose addresses are referenced via short PUSH so the
    # funded account lands at the literal address (e.g. precompile
    # 0x01) instead of a random ``pre.fund_eoa`` address.
    for acct in raw_accounts:
        if acct.address in short_push_eoa_refs:
            acct.use_dynamic = False

    # Pin EOAs whose tags were hint-overridden into the precompile
    # range. The override registered the literal address in
    # ``addr_to_var`` so tx-data and post-state resolutions point at
    # ``addr_X`` (a variable). The variable must hold the literal
    # precompile address at runtime, not whatever ``pre.fund_eoa``
    # picks.
    for acct in raw_accounts:
        if acct.address in pinned_eoa_addrs:
            acct.use_dynamic = False

    # ------------------------------------------------------------------
    # Pass 2: convert bytecode to Op expressions
    # ------------------------------------------------------------------
    # Collect all address variable names for arithmetic detection
    addr_var_names = set(addr_to_var.values())

    for acct in raw_accounts:
        cb = code_bytes_map.get(acct.address) if acct.address else None
        if not cb:
            continue
        try:
            if acct.use_dynamic:
                # Try with addr_to_var for symbolic references
                op_expr = _bytes_to_op_expr(cb, addr_to_var)
                if op_expr is None:
                    # Fallback: without addr_to_var (keep dynamic)
                    op_expr = _bytes_to_op_expr(cb)
            else:
                op_expr = _bytes_to_op_expr(cb)

            if op_expr:
                acct.code_expr = op_expr
                imports.needs_op = True
            elif cb:
                acct.code_expr = f'bytes.fromhex("{cb.hex()}")'
        except Exception:
            acct.code_expr = 'b""'

    # ------------------------------------------------------------------
    # Check for address variables used in arithmetic operations.
    # Pattern: Op.ADD(contract_0, ...) means contracts are at
    # sequential addresses and cannot be dynamically assigned.
    # If found, disable dynamic for ALL contracts.
    # ------------------------------------------------------------------
    arith_ops = {"Op.ADD(", "Op.SUB(", "Op.MUL(", "Op.DIV("}
    has_addr_arithmetic = False
    for acct in raw_accounts:
        if not acct.code_expr:
            continue
        for var_name in addr_var_names:
            for arith_op in arith_ops:
                if f"{arith_op}{var_name}" in acct.code_expr:
                    has_addr_arithmetic = True
                    break
            if has_addr_arithmetic:
                break
        if has_addr_arithmetic:
            break

    # ------------------------------------------------------------------
    # Computed call targets: CALL/STATICCALL/DELEGATECALL/CALLCODE
    # receiving `address=` from arithmetic or memory reads. Tests that
    # do this usually rely on specific pre-state contract addresses
    # (dispatch-by-offset) and won't survive dynamic allocation.
    # ------------------------------------------------------------------
    computed_addr_patterns = (
        "address=Op.ADD(",
        "address=Op.SUB(",
        "address=Op.MUL(",
        "address=Op.DIV(",
        "address=Op.MOD(",
        "address=Op.MLOAD(",
        "address=Op.SLOAD(",
        "address=Op.CALLDATALOAD(",
    )
    has_computed_call_target = False
    for acct in raw_accounts:
        if not acct.code_expr:
            continue
        for pat in computed_addr_patterns:
            if pat in acct.code_expr:
                has_computed_call_target = True
                break
        if has_computed_call_target:
            break

    if (
        has_addr_arithmetic
        or short_push_unpinnable
        or has_computed_call_target
        or force_hardcoded
    ):
        # Disable dynamic for all contracts and re-generate Op
        # expressions without addr_to_var. Triggers:
        #   * address arithmetic (Op.ADD(var, ...)) assumes sequential
        #     addresses that dynamic allocation can't preserve.
        #   * a short-PUSH ref that points outside the pre-state has no
        #     contract to pin, so the whole test must keep the filler's
        #     resolved addresses.
        #   * computed call targets (CALL with address=Op.ADD/MLOAD/
        #     CALLDATALOAD/...) dispatch by baseline-relative offsets.
        #   * the test is on the FORCE_HARDCODED_TESTS allowlist — we've
        #     accepted that it can't converge under exact-no-stack with
        #     dynamic addresses (see module docstring on that set).
        for acct in raw_accounts:
            if not acct.is_eoa:
                acct.use_dynamic = False
            cb = code_bytes_map.get(acct.address) if acct.address else None
            if not cb:
                continue
            try:
                op_expr = _bytes_to_op_expr(cb)
                if op_expr:
                    acct.code_expr = op_expr
                elif cb:
                    acct.code_expr = f'bytes.fromhex("{cb.hex()}")'
            except Exception:
                acct.code_expr = 'b""'

    # ------------------------------------------------------------------
    # Reorder: EOAs first (filler order), then contracts (topo order)
    # ------------------------------------------------------------------
    eoa_accounts = [a for a in raw_accounts if a.is_eoa]
    contract_by_addr = {a.address: a for a in raw_accounts if not a.is_eoa}
    # Sorted contracts first, then any cycle contracts in filler order
    ordered_contracts: list[AccountIR] = []
    for addr in sorted_addrs:
        if addr in contract_by_addr:
            ordered_contracts.append(contract_by_addr[addr])
    # Append cycle contracts (non-dynamic) in their original filler order
    for acct in raw_accounts:
        if not acct.is_eoa and acct.address in cycle_addrs:
            ordered_contracts.append(acct)

    return eoa_accounts + ordered_contracts


def _build_environment(
    model: StateStaticTest,
    tags: TagDict,
    addr_to_var: dict[Address | EOA, str],
) -> EnvironmentIR:
    """Build EnvironmentIR."""
    # Resolve coinbase
    if isinstance(model.env.current_coinbase, Tag):
        tag_name = model.env.current_coinbase.name
        resolved = tags.get(tag_name)
        coinbase_var = (
            addr_to_var.get(resolved, tag_name) if resolved else tag_name
        )
    else:
        coinbase_var = addr_to_var.get(model.env.current_coinbase, "coinbase")

    return EnvironmentIR(
        coinbase_var=coinbase_var,
        number=int(model.env.current_number),
        timestamp=int(model.env.current_timestamp),
        difficulty=(
            int(model.env.current_difficulty)
            if model.env.current_difficulty is not None
            else None
        ),
        prev_randao=(
            int(model.env.current_random)
            if model.env.current_random is not None
            else None
        ),
        base_fee_per_gas=(
            int(model.env.current_base_fee)
            if model.env.current_base_fee is not None
            else None
        ),
        excess_blob_gas=(
            int(model.env.current_excess_blob_gas)
            if model.env.current_excess_blob_gas is not None
            else None
        ),
        gas_limit=int(model.env.current_gas_limit),
    )


def _fork_set_to_constraints(
    fork_set: ForkSet, all_fork_names: list[str]
) -> list[str]:
    """Reconstruct constraint strings from an expanded ForkSet."""
    set_fork_names = sorted(
        [str(f) for f in fork_set],
        key=lambda f: all_fork_names.index(f) if f in all_fork_names else 999,
    )

    if not set_fork_names:
        return []

    if len(set_fork_names) == 1:
        return [set_fork_names[0]]

    # Try to detect contiguous ranges
    groups: list[list[str]] = []
    group: list[str] = [set_fork_names[0]]
    for i in range(1, len(set_fork_names)):
        curr_idx = all_fork_names.index(set_fork_names[i])
        prev_idx = all_fork_names.index(set_fork_names[i - 1])
        if curr_idx == prev_idx + 1:
            group.append(set_fork_names[i])
        else:
            groups.append(group)
            group = [set_fork_names[i]]
    groups.append(group)

    constraints: list[str] = []
    for g in groups:
        if len(g) == 1:
            constraints.append(g[0])
        else:
            last_idx = all_fork_names.index(g[-1])
            if last_idx == len(all_fork_names) - 1:
                constraints.append(f">={g[0]}")
            else:
                next_fork = all_fork_names[last_idx + 1]
                constraints.append(f">={g[0]}<{next_fork}")
    return constraints


def _format_exception_value(
    exc: Any,
) -> str:
    """Format a TransactionException value as a Python expression string."""
    if isinstance(exc, list):
        parts = [f"TransactionException.{e.name}" for e in exc]
        return "[" + ", ".join(parts) + "]"
    if isinstance(exc, TransactionException):
        return f"TransactionException.{exc.name}"
    return str(exc)


def _build_expect_entries(
    model: StateStaticTest,
    tags: TagDict,
    addr_to_var: dict[Address | EOA, str],
    all_fork_names: list[str],
    imports: ImportsIR,
) -> list[ExpectEntryIR]:
    """Build ExpectEntryIR list."""
    entries: list[ExpectEntryIR] = []

    for expect in model.expect:
        # Indexes
        indexes = {
            "data": expect.indexes.data,
            "gas": expect.indexes.gas,
            "value": expect.indexes.value,
        }

        # Network constraints
        network = _fork_set_to_constraints(expect.network, all_fork_names)

        # Result: resolve and map to assertions
        result_assertions: list[AccountAssertionIR] = []
        for address_or_tag, account_expect in expect.result.root.items():
            if isinstance(address_or_tag, Tag):
                # Use resolve() for all tags — handles CreateTag's
                # address derivation (compute_create_address etc.)
                try:
                    addr = address_or_tag.resolve(tags)
                    var_ref = _resolve_address(addr, addr_to_var, imports)
                except (KeyError, AssertionError):
                    tag_name = address_or_tag.name
                    addr = tags.get(tag_name, tag_name)
                    assert not isinstance(addr, str)
                    var_ref = _resolve_address(addr, addr_to_var, imports)
            else:
                var_ref = _resolve_address(
                    address_or_tag, addr_to_var, imports
                )

            if account_expect is None:
                # shouldnotexist
                result_assertions.append(
                    AccountAssertionIR(
                        var_ref=var_ref,
                        should_not_exist=True,
                    )
                )
                continue

            # Storage (including ANY keys)
            storage: dict[int, int | str] | None = None
            storage_any_keys: list[int] = []
            if account_expect.storage is not None:
                storage = {}
                resolved_storage = account_expect.storage.resolve(tags)
                for k, v in resolved_storage.items():
                    storage[int(k)] = int(v)
                storage = _resolve_storage_values(
                    storage, addr_to_var, imports
                )
                # Capture ANY keys from _any_map
                if hasattr(resolved_storage, "_any_map"):
                    for k in resolved_storage._any_map:
                        storage_any_keys.append(int(k))

            # Code
            code: bytes | None = None
            if account_expect.code is not None:
                try:
                    code = account_expect.code.compiled(tags)
                except Exception:
                    pass

            result_assertions.append(
                AccountAssertionIR(
                    var_ref=var_ref,
                    storage=storage,
                    storage_any_keys=storage_any_keys,
                    code=code,
                    balance=(
                        int(account_expect.balance)
                        if account_expect.balance is not None
                        else None
                    ),
                    nonce=(
                        int(account_expect.nonce)
                        if account_expect.nonce is not None
                        else None
                    ),
                )
            )

        # Exception
        expect_exc: dict[str, str] | None = None
        if expect.expect_exception is not None:
            expect_exc = {}
            for fork_set_key in expect.expect_exception:
                constraint_strs = _fork_set_to_constraints(
                    fork_set_key, all_fork_names
                )
                constraint_key = ",".join(constraint_strs)
                exc_value = expect.expect_exception.root[fork_set_key]
                expect_exc[constraint_key] = _format_exception_value(exc_value)

        entries.append(
            ExpectEntryIR(
                indexes=indexes,
                network=network,
                result=result_assertions,
                expect_exception=expect_exc,
            )
        )

    return entries


def _build_transaction_ir(
    model: StateStaticTest,
    tags: TagDict,
    addr_to_var: dict[Address | EOA, str],
    tx_data: list[str],
    tx_gas: list[int],
    tx_value: list[int],
    is_multi_case: bool,
    imports: ImportsIR,
) -> tuple[TransactionIR, list[AccessListEntryIR]]:
    """Build TransactionIR. Return (transaction_ir, access_list_entries)."""
    # Resolve "to"
    to_var: str | None = None
    to_is_none = False
    if model.transaction.to is None:
        to_is_none = True
    elif isinstance(model.transaction.to, Tag):
        tag_name = model.transaction.to.name
        resolved = tags.get(tag_name)
        if resolved:
            to_var = addr_to_var.get(resolved, tag_name)
        else:
            to_var = tag_name
    else:
        to_var = _resolve_address(model.transaction.to, addr_to_var, imports)

    # Access lists — check if they vary per data entry
    access_list_entries: list[AccessListEntryIR] = []
    per_data_access_lists: dict[int, list[AccessListEntryIR]] | None = None

    def _resolve_access_list(data_box_al):
        entries = []
        for al_entry in data_box_al:
            if isinstance(al_entry.address, Tag):
                resolved_al = al_entry.address.resolve(tags)
                al_address = Address(resolved_al)
            else:
                al_address = al_entry.address
            # Try to resolve to variable name
            var_name = addr_to_var.get(al_address)
            if var_name:
                al_addr_str = var_name
                al_dynamic = True
            else:
                al_addr_str = str(al_address)
                al_dynamic = False
            al_keys = [str(k) for k in al_entry.storage_keys]
            entries.append(
                AccessListEntryIR(
                    address=al_addr_str,
                    storage_keys=al_keys,
                    use_dynamic=al_dynamic,
                )
            )
        return entries

    # Check if any data entry has access lists
    has_any_al = any(
        model.transaction.data[d.index].access_list is not None
        for d in model.transaction.data
    )
    if has_any_al and is_multi_case:
        # Build per-data access list map.
        # Include entries where access_list is not None (even if empty [])
        # because access_list=[] makes the tx type-2 (EIP-2930), while
        # access_list=None keeps it legacy.
        per_data_al: dict[int, list[AccessListEntryIR]] = {}
        for d in model.transaction.data:
            data_box = model.transaction.data[d.index]
            if data_box.access_list is not None:
                per_data_al[d.index] = _resolve_access_list(
                    data_box.access_list
                )
        if per_data_al:
            per_data_access_lists = per_data_al
    elif has_any_al:
        # Single-case: use first data entry's access list
        first_data = model.transaction.data[0]
        if first_data.access_list is not None:
            access_list_entries = _resolve_access_list(first_data.access_list)

    # Blob versioned hashes
    blob_hashes: list[str] | None = None
    if model.transaction.blob_versioned_hashes is not None:
        blob_hashes = [str(h) for h in model.transaction.blob_versioned_hashes]

    # Single-case inlines
    data_inline: str | None = None
    gas_limit_single: int | None = None
    value_single: int | None = None
    if not is_multi_case:
        if tx_data and tx_data[0]:
            data_inline = tx_data[0]
        else:
            data_inline = "b''"
        gas_limit_single = tx_gas[0] if tx_gas else 21000
        value_single = tx_value[0] if tx_value else 0

    return (
        TransactionIR(
            to_var=to_var,
            to_is_none=to_is_none,
            gas_price=(
                int(model.transaction.gas_price)
                if model.transaction.gas_price is not None
                else None
            ),
            max_fee_per_gas=(
                int(model.transaction.max_fee_per_gas)
                if model.transaction.max_fee_per_gas is not None
                else None
            ),
            max_priority_fee_per_gas=(
                int(model.transaction.max_priority_fee_per_gas)
                if model.transaction.max_priority_fee_per_gas is not None
                else None
            ),
            max_fee_per_blob_gas=(
                int(model.transaction.max_fee_per_blob_gas)
                if model.transaction.max_fee_per_blob_gas is not None
                else None
            ),
            blob_versioned_hashes=blob_hashes,
            nonce=(
                int(model.transaction.nonce)
                if model.transaction.nonce is not None
                else None
            ),
            access_list=access_list_entries if has_any_al else None,
            per_data_access_lists=per_data_access_lists,
            data_inline=data_inline,
            gas_limit=gas_limit_single,
            value=value_single,
        ),
        access_list_entries,
    )


def _build_address_constants(
    model: StateStaticTest,
    tags: TagDict,
    addr_to_var: dict[Address | EOA, str],
    sender_tag_name: str | None,
    accounts: list[AccountIR],
) -> list[dict[str, str]]:
    """Build list of address constants for the function body."""
    constants: list[dict[str, str]] = []
    seen: set[Address | EOA] = set()

    # Collect addresses of dynamic EOAs — these are handled by
    # pre.fund_eoa() in the accounts section, not as constants.
    dynamic_eoa_addrs: set[Address | EOA] = set()
    for acct in accounts:
        if acct.is_eoa and acct.use_dynamic and acct.address is not None:
            dynamic_eoa_addrs.add(acct.address)

    # Coinbase (tagged or not) — always keep as hardcoded constant
    if isinstance(model.env.current_coinbase, Tag):
        tag_name = model.env.current_coinbase.name
        resolved = tags.get(tag_name)
        if resolved:
            var_name = addr_to_var.get(resolved, "coinbase")
            if var_name != "sender" and resolved not in seen:
                constants.append({"var_name": var_name, "hex": f"{resolved}"})
                seen.add(resolved)
    else:
        addr = model.env.current_coinbase
        var_name = addr_to_var.get(model.env.current_coinbase)
        if var_name and var_name != "sender" and addr not in seen:
            constants.append({"var_name": var_name, "hex": f"{addr}"})
            seen.add(addr)

    # All non-sender, non-contract pre-state accounts (tagged or not)
    for address_or_tag, _acct in model.pre.root.items():
        if isinstance(address_or_tag, Tag):
            tag_name = address_or_tag.name
            # Skip sender
            if sender_tag_name and tag_name == sender_tag_name:
                continue
            # Skip ContractTag accounts (they get address via deploy_contract)
            # SenderTag accounts are EOAs even if they have code
            if isinstance(address_or_tag, ContractTag):
                continue
            resolved = tags.get(tag_name)
            if resolved:
                # Skip dynamic EOAs (handled by fund_eoa)
                if resolved in dynamic_eoa_addrs:
                    continue
                var_name = addr_to_var.get(resolved, tag_name)
                if resolved not in seen and var_name != "coinbase":
                    constants.append(
                        {"var_name": var_name, "hex": f"{resolved}"}
                    )
                    seen.add(resolved)
        else:
            # Skip dynamic EOAs (handled by fund_eoa)
            if address_or_tag in dynamic_eoa_addrs:
                continue
            var_name = addr_to_var.get(address_or_tag)
            if (
                var_name
                and var_name != "sender"
                and var_name != "coinbase"
                and address_or_tag not in seen
            ):
                constants.append(
                    {"var_name": var_name, "hex": f"{address_or_tag}"}
                )
                seen.add(address_or_tag)

    return constants


def _decode_tx_data_word(
    data: bytes, addr_to_var: dict[Address | EOA, str], imports: ImportsIR
) -> str:
    """
    Attempt to decode a single word of 32 or 20 bytes from the transaction
    data into meaningful information.
    """
    addr_var: str | None = None
    if len(data.lstrip(b"\x00")) <= 20:
        maybe_addr = Address(int.from_bytes(data, "big"))
        if maybe_addr in addr_to_var:
            addr_var = addr_to_var[maybe_addr]

    if len(data) == 32 or len(data) == 20:
        if addr_var:
            if len(data) == 20:
                return addr_var
            else:
                imports.needs_hash = True
                return f"Hash({addr_var}, left_padding=True)"
        else:
            if len(data) == 32:
                imports.needs_hash = True
                hex_type = "Hash"
            else:
                hex_type = "Address"
            hex_string = data.hex().lstrip("0")
            if len(hex_string) == 0:
                hex_string = "0"
            return f"{hex_type}(0x{hex_string})"
    else:
        imports.needs_bytes = True
        hex_string = data.hex()
        return f'Bytes("{hex_string}")'


def _decode_tx_data(
    data: bytes,
    addr_to_var: dict[Address | EOA, str],
    probably_bytecode: bool,
    imports: ImportsIR,
) -> str:
    """Attempt to decode meaningful information from the transaction data."""
    if probably_bytecode:
        bytecode = _bytes_to_op_expr(data, addr_to_var)
        if bytecode:
            imports.needs_op = True
            return bytecode
    decoded_words: list[str] = []
    if len(data) > 0 and len(data) % 32 in (0, 4):
        if len(data) % 32 == 4:
            decoded_words.append(
                _decode_tx_data_word(data[:4], addr_to_var, imports)
            )
        offset = 4 if len(data) % 32 == 4 else 0
        for i in range(offset, len(data), 32):
            decoded_words.append(
                _decode_tx_data_word(data[i : i + 32], addr_to_var, imports)
            )
    else:
        return _decode_tx_data_word(data, addr_to_var, imports)
    return " + ".join(decoded_words)


def _build_tx_arrays(
    tx: GeneralTransactionInFiller,
    tags: TagDict,
    addr_to_var: dict[Address | EOA, str],
    probably_bytecode: bool,
    imports: ImportsIR,
) -> tuple[list[str], list[int], list[int]]:
    """Build the list of data that goes in each transaction."""
    tx_data: list[str] = []
    for d_entry in tx.data:
        data_box = tx.data[d_entry.index]
        compiled = data_box.data.compiled(tags)
        tx_data.append(
            _decode_tx_data(compiled, addr_to_var, probably_bytecode, imports)
        )

    tx_gas = [int(g) for g in tx.gas_limit]
    tx_value = [int(v) for v in tx.value]
    return tx_data, tx_gas, tx_value


def _resolve_address(
    addr: Address,
    addr_to_var: dict[Address | EOA, str],
    imports: ImportsIR,
) -> str:
    """
    Return a variable reference if the address or an address derived from it
    is contained in the `addr_to_var` dictionary.

    Fallbacks to returning f"Address({addr})".
    """
    for var_addr, var in addr_to_var.items():
        if addr == var_addr:
            return var
    # Check if the address is the result of contract creation from a known
    # address.  Use a larger range to cover high-nonce senders.
    for var_addr, var in addr_to_var.items():
        for nonce in range(10000):
            if addr == compute_create_address(address=var_addr, nonce=nonce):
                imports.needs_compute_create_address = True
                return f"compute_create_address(address={var}, nonce={nonce})"

    # Nested CREATE: address created by a contract that was itself created
    # by a known address (2 levels deep, small nonce range to keep
    # generation fast — most contracts CREATE only a few children).
    for var_addr, var in addr_to_var.items():
        for n1 in range(16):
            child = compute_create_address(address=var_addr, nonce=n1)
            for n2 in range(16):
                if addr == compute_create_address(address=child, nonce=n2):
                    imports.needs_compute_create_address = True
                    return (
                        f"compute_create_address("
                        f"address=compute_create_address("
                        f"address={var}, nonce={n1}), nonce={n2})"
                    )

    return f"Address({addr})"
