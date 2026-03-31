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
    accounts = _build_accounts(
        model, tags, addr_to_var, sender_tag_name, imports
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
        model, tags, addr_to_var, sender_tag_name
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
        # Find sender balance from pre-state
        balance = 0
        for address_or_tag, account in model.pre.root.items():
            if isinstance(address_or_tag, SenderTag):
                if address_or_tag.name == tag_name:
                    balance = int(account.balance) if account.balance else 0
                    break
        return (
            SenderIR(is_tagged=False, key=key_int, balance=balance),
            tag_name,
        )
    else:
        # Find sender balance from pre-state
        eoa = EOA(key=model.transaction.secret_key)
        sender_addr = _addr_hex(eoa)
        balance = 0
        for address_or_tag, account in model.pre.root.items():
            if not isinstance(address_or_tag, Tag):
                if _addr_hex(address_or_tag) == sender_addr:
                    balance = int(account.balance) if account.balance else 0
                    break
        return SenderIR(
            is_tagged=False,
            key=int.from_bytes(eoa.key, "big"),
            balance=balance,
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


def _build_accounts(
    model: StateStaticTest,
    tags: TagDict,
    addr_to_var: dict[Address | EOA, str],
    sender_tag_name: str | None,
    imports: ImportsIR,
) -> list[AccountIR]:
    """Build AccountIR list. Return (accounts, needs_op_import)."""
    accounts: list[AccountIR] = []

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

        # Code processing
        source_comment = ""
        code_expr = ""
        oversized_code = False
        if has_code:
            source_comment = _classify_code_source(account.code.source)
            try:
                code_bytes = account.code.compiled(tags)
                if len(code_bytes) > MAX_BYTECODE_OP_SIZE:
                    oversized_code = True
                # TODO: To add `addr_to_var` here, we need to resolve
                # dependency order.
                op_expr = _bytes_to_op_expr(code_bytes)
                if op_expr:
                    code_expr = op_expr
                    imports.needs_op = True
                elif code_bytes:
                    code_expr = f'bytes.fromhex("{code_bytes.hex()}")'
            except Exception as e:
                warnings.warn(
                    f"Code compilation failed for {var_name}: {e}",
                    stacklevel=2,
                )
                code_expr = 'b""'

        # Storage
        storage: dict[int, int] = {}
        if account.storage and account.storage.root:
            resolved_storage = account.storage.resolve(tags)
            for k, v in resolved_storage.items():
                storage[int(k)] = int(v)

        # Balance and nonce
        balance = int(account.balance) if account.balance is not None else 0
        nonce = int(account.nonce) if account.nonce is not None else None

        accounts.append(
            AccountIR(
                var_name=var_name,
                is_tagged=is_tagged,
                is_eoa=is_eoa,
                is_sender=is_sender,
                balance=balance,
                nonce=nonce,
                address=address,
                source_comment=source_comment,
                code_expr=code_expr,
                storage=storage,
                oversized_code=oversized_code,
            )
        )

    return accounts


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
            storage: dict[int, int] | None = None
            storage_any_keys: list[int] = []
            if account_expect.storage is not None:
                storage = {}
                resolved_storage = account_expect.storage.resolve(tags)
                for k, v in resolved_storage.items():
                    storage[int(k)] = int(v)
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
                al_addr = str(Address(resolved_al))
            else:
                al_addr = str(al_entry.address)
            al_keys = [str(k) for k in al_entry.storage_keys]
            entries.append(
                AccessListEntryIR(address=al_addr, storage_keys=al_keys)
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
) -> list[dict[str, str]]:
    """Build list of address constants for the function body."""
    constants: list[dict[str, str]] = []
    seen: set[Address | EOA] = set()

    # Coinbase (tagged or not)
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
                var_name = addr_to_var.get(resolved, tag_name)
                if resolved not in seen and var_name != "coinbase":
                    constants.append(
                        {"var_name": var_name, "hex": f"{resolved}"}
                    )
                    seen.add(resolved)
        else:
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
    # address.
    for var_addr, var in addr_to_var.items():
        max_created_contracts = 256
        for nonce in range(max_created_contracts):
            if addr == compute_create_address(address=var_addr, nonce=nonce):
                imports.needs_compute_create_address = True
                return f"compute_create_address(address={var}, nonce={nonce})"

    return f"Address({addr})"
