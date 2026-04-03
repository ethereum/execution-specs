"""Intermediate Representation dataclasses for filler-to-python codegen."""

from __future__ import annotations

from dataclasses import dataclass, field

from execution_testing.base_types import Address


@dataclass
class EnvironmentIR:
    """IR for the test environment."""

    coinbase_var: str
    number: int
    timestamp: int
    difficulty: int | None = None
    prev_randao: int | None = None
    base_fee_per_gas: int | None = None
    excess_blob_gas: int | None = None
    gas_limit: int = 0


@dataclass
class AccountIR:
    """IR for a pre-state account."""

    var_name: str
    is_tagged: bool
    is_eoa: bool
    is_sender: bool
    balance: int = 0
    nonce: int | None = None
    address: Address | None = None
    source_comment: str = ""
    code_expr: str = ""
    storage: dict = field(default_factory=dict)
    oversized_code: bool = False


@dataclass
class AccountAssertionIR:
    """IR for a post-state account assertion."""

    var_ref: str
    storage: dict | None = None
    storage_any_keys: list = field(default_factory=list)
    code: bytes | None = None
    balance: int | None = None
    nonce: int | None = None
    should_not_exist: bool = False


@dataclass
class ExpectEntryIR:
    """IR for one filler expect section."""

    indexes: dict = field(default_factory=dict)
    network: list = field(default_factory=list)
    result: list = field(default_factory=list)
    expect_exception: dict | None = None


@dataclass
class ParameterCaseIR:
    """IR for one (d, g, v) parameter combo."""

    d: int = 0
    g: int = 0
    v: int = 0
    has_exception: bool = False
    label: str | None = None
    id: str = ""
    marks: str | None = None


@dataclass
class AccessListEntryIR:
    """IR for a single access list entry."""

    address: str = ""
    storage_keys: list = field(default_factory=list)


@dataclass
class TransactionIR:
    """IR for the transaction."""

    to_var: str | None = None
    to_is_none: bool = False
    gas_price: int | None = None
    max_fee_per_gas: int | None = None
    max_priority_fee_per_gas: int | None = None
    max_fee_per_blob_gas: int | None = None
    blob_versioned_hashes: list | None = None
    nonce: int | None = None
    access_list: list | None = None
    per_data_access_lists: dict | None = None
    data_inline: str | None = None
    gas_limit: int | None = None
    value: int | None = None


@dataclass
class SenderIR:
    """IR for the transaction sender."""

    is_tagged: bool = False
    key: int | None = None
    balance: int = 0
    not_in_pre: bool = False


@dataclass
class ImportsIR:
    """List of import requirements for the test."""

    needs_op: bool = False
    needs_access_list: bool = False
    needs_bytes: bool = False
    needs_hash: bool = False
    needs_tx_exception: bool = False
    needs_compute_create_address: bool = False


@dataclass
class IntermediateTestModel:
    """Complete IR for one test file."""

    test_name: str = ""
    filler_path: str = ""
    filler_comment: str = ""
    category: str = ""
    valid_from: str = ""
    valid_until: str | None = None
    is_slow: bool = False
    is_multi_case: bool = False
    is_fork_dependent: bool = False
    environment: EnvironmentIR = field(
        default_factory=lambda: EnvironmentIR(
            coinbase_var="coinbase", number=0, timestamp=0
        )
    )
    accounts: list = field(default_factory=list)
    sender: SenderIR = field(default_factory=SenderIR)
    parameters: list = field(default_factory=list)
    transaction: TransactionIR = field(default_factory=TransactionIR)
    expect_entries: list = field(default_factory=list)
    address_constants: list = field(default_factory=list)
    tx_data: list = field(default_factory=list)
    tx_gas: list = field(default_factory=list)
    tx_value: list = field(default_factory=list)
    imports: ImportsIR = field(default_factory=ImportsIR)
