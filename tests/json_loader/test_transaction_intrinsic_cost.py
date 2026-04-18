"""Regression tests for Amsterdam intrinsic and floor gas calculation."""

from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U8, U64, U256, Uint

from ethereum.forks.amsterdam.fork_types import Authorization
from ethereum.forks.amsterdam.transactions import (
    GAS_TX_ACCESS_LIST_ADDRESS,
    GAS_TX_ACCESS_LIST_STORAGE_KEY,
    GAS_TX_BASE,
    GAS_TX_CREATE,
    GAS_TX_DATA_TOKEN_FLOOR,
    GAS_TX_DATA_TOKEN_STANDARD,
    Access,
    AccessListTransaction,
    LegacyTransaction,
    SetCodeTransaction,
    calculate_intrinsic_cost,
    count_tokens_in_data,
)
from ethereum.forks.amsterdam.vm.eoa_delegation import (
    GAS_AUTH_PER_EMPTY_ACCOUNT,
)
from ethereum.forks.amsterdam.vm.gas import init_code_cost
from ethereum.state import Address


def test_legacy_tx_intrinsic_and_floor_gas() -> None:
    """Legacy calldata cost keeps standard and floor accounting separate."""
    tx = LegacyTransaction(
        nonce=U256(0),
        gas_price=Uint(1),
        gas=Uint(100000),
        to=Address(b"\x11" * 20),
        value=U256(0),
        data=Bytes(b"\x00\x01\x00\x02"),
        v=U256(27),
        r=U256(1),
        s=U256(2),
    )

    tokens_in_calldata = count_tokens_in_data(tx.data)

    intrinsic_gas, floor_gas = calculate_intrinsic_cost(tx)

    assert intrinsic_gas == Uint(
        GAS_TX_BASE + tokens_in_calldata * GAS_TX_DATA_TOKEN_STANDARD
    )
    assert floor_gas == Uint(
        GAS_TX_BASE + tokens_in_calldata * GAS_TX_DATA_TOKEN_FLOOR
    )


def test_contract_creation_intrinsic_gas_includes_create_cost() -> None:
    """Contract creation includes both create gas and initcode metering."""
    tx = LegacyTransaction(
        nonce=U256(0),
        gas_price=Uint(1),
        gas=Uint(200000),
        to=Bytes(b""),
        value=U256(0),
        data=Bytes(b"\x60\x00\x60\x00"),
        v=U256(27),
        r=U256(1),
        s=U256(2),
    )

    tokens_in_calldata = count_tokens_in_data(tx.data)

    intrinsic_gas, floor_gas = calculate_intrinsic_cost(tx)

    assert intrinsic_gas == Uint(
        GAS_TX_BASE
        + tokens_in_calldata * GAS_TX_DATA_TOKEN_STANDARD
        + GAS_TX_CREATE
        + init_code_cost(Uint(len(tx.data)))
    )
    assert floor_gas == Uint(
        GAS_TX_BASE + tokens_in_calldata * GAS_TX_DATA_TOKEN_FLOOR
    )


def test_access_list_intrinsic_gas_excludes_access_list_floor_tokens() -> None:
    """Amsterdam access lists affect intrinsic gas but not floor tokens."""
    tx = AccessListTransaction(
        chain_id=U64(1),
        nonce=U256(0),
        gas_price=Uint(1),
        gas=Uint(200000),
        to=Address(b"\x22" * 20),
        value=U256(0),
        data=Bytes(b"\x01\x00"),
        access_list=(
            Access(
                account=Address(b"\x33" * 20),
                slots=(Bytes(b"\x00" * 32), Bytes(b"\x01" * 32)),
            ),
        ),
        y_parity=U256(0),
        r=U256(1),
        s=U256(2),
    )

    tokens_in_calldata = count_tokens_in_data(tx.data)

    intrinsic_gas, floor_gas = calculate_intrinsic_cost(tx)

    assert intrinsic_gas == Uint(
        GAS_TX_BASE
        + tokens_in_calldata * GAS_TX_DATA_TOKEN_STANDARD
        + GAS_TX_ACCESS_LIST_ADDRESS
        + Uint(2) * GAS_TX_ACCESS_LIST_STORAGE_KEY
    )
    assert floor_gas == Uint(
        GAS_TX_BASE + tokens_in_calldata * GAS_TX_DATA_TOKEN_FLOOR
    )


def test_set_code_tx_intrinsic_gas_includes_authorization_cost() -> None:
    """Set-code transactions charge per authorization in intrinsic gas."""
    tx = SetCodeTransaction(
        chain_id=U64(1),
        nonce=U64(0),
        max_priority_fee_per_gas=Uint(1),
        max_fee_per_gas=Uint(1),
        gas=Uint(300000),
        to=Address(b"\x44" * 20),
        value=U256(0),
        data=Bytes(b"\x01"),
        access_list=(),
        authorizations=(
            Authorization(
                chain_id=U256(1),
                address=Address(b"\x55" * 20),
                nonce=U64(0),
                y_parity=U8(0),
                r=U256(1),
                s=U256(2),
            ),
            Authorization(
                chain_id=U256(1),
                address=Address(b"\x66" * 20),
                nonce=U64(1),
                y_parity=U8(1),
                r=U256(3),
                s=U256(4),
            ),
        ),
        y_parity=U256(0),
        r=U256(1),
        s=U256(2),
    )

    tokens_in_calldata = count_tokens_in_data(tx.data)

    intrinsic_gas, floor_gas = calculate_intrinsic_cost(tx)

    assert intrinsic_gas == Uint(
        GAS_TX_BASE
        + tokens_in_calldata * GAS_TX_DATA_TOKEN_STANDARD
        + Uint(GAS_AUTH_PER_EMPTY_ACCOUNT * 2)
    )
    assert floor_gas == Uint(
        GAS_TX_BASE + tokens_in_calldata * GAS_TX_DATA_TOKEN_FLOOR
    )
