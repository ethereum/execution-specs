"""Test suite for `CreatePreimageLayout`."""

import pytest

from execution_testing.base_types import Account, Address
from execution_testing.client_clis import TransitionTool
from execution_testing.fixtures import (
    StateFixture,
)
from execution_testing.forks import get_deployed_forks
from execution_testing.specs import StateTest
from execution_testing.test_types import (
    EOA,
    Alloc,
    Transaction,
    compute_create2_address,
    compute_create_address,
)
from execution_testing.vm import Bytecode, Op

from ..tools_code.generators import Create2PreimageLayout, CreatePreimageLayout


@pytest.mark.parametrize(
    "offset",
    [
        pytest.param(0, id="zero-offset"),
        pytest.param(32, id="32-offset"),
        pytest.param(100, id="100-offset"),
    ],
)
def test_create_preimage_layout_nonce_offset(offset: int) -> None:
    """Test `CreatePreimageLayout.nonce_offset` equals offset + 32."""
    layout = CreatePreimageLayout(
        sender_address=0xDEADBEEF,
        nonce=Op.PUSH1(1),
        offset=offset,
    )
    assert layout.nonce_offset == offset + 32


def test_create_preimage_layout_dynamic_address_op() -> None:
    """Test that dynamic address_op uses MLOAD for preimage size."""
    layout = CreatePreimageLayout(
        sender_address=0xDEADBEEF,
        nonce=Op.CALLDATALOAD(0),
    )
    address_mask = (1 << 160) - 1
    expected = Op.AND(
        address_mask,
        Op.SHA3(
            offset=10,
            size=Op.MLOAD(64),
            data_size=25,
        ),
    )
    assert bytes(layout.address_op()) == bytes(expected)


def test_create_preimage_layout_set_nonce_op() -> None:
    """Test that set_nonce_op returns valid Bytecode."""
    layout = CreatePreimageLayout(
        sender_address=0xDEADBEEF,
        nonce=Op.CALLDATALOAD(0),
    )
    result = layout.set_nonce_op(42)
    assert len(result) > 0


def test_create_preimage_layout_increment_nonce_op() -> None:
    """Test that increment_nonce_op returns valid Bytecode."""
    layout = CreatePreimageLayout(
        sender_address=0xDEADBEEF,
        nonce=Op.CALLDATALOAD(0),
    )
    result = layout.increment_nonce_op()
    assert len(result) > 0


@pytest.mark.parametrize(
    "offset,creator_address",
    [
        pytest.param(0, None, id="zero-offset"),
        pytest.param(1, None, id="one-offset"),
        pytest.param(32, None, id="32-offset"),
        pytest.param(0, 0x2000, id="different-creator-address"),
    ],
)
def test_create_preimage(
    default_t8n: TransitionTool,
    offset: int,
    creator_address: int | None,
) -> None:
    """Test `CreatePreimageLayout` by running its result in the EVM."""
    sender = EOA(key=1)

    contract_address = 0x1000
    creator_address = (
        contract_address if creator_address is None else creator_address
    )
    create_preimage = CreatePreimageLayout(
        sender_address=Op.ADDRESS
        if creator_address == contract_address
        else creator_address,
        nonce=1,
        offset=offset,
    )
    contract: Bytecode = (
        create_preimage
        + Op.SSTORE(1, create_preimage.address_op())
        + create_preimage.increment_nonce_op()
        + Op.SSTORE(2, create_preimage.address_op())
        + create_preimage.set_nonce_op(10)
        + Op.SSTORE(10, create_preimage.address_op())
    )

    pre = Alloc(
        {
            sender: Account(balance=(10**18)),
            Address(contract_address): Account(code=contract),
        }
    )
    post = Alloc(
        {
            Address(contract_address): Account(
                storage={
                    1: compute_create_address(
                        address=creator_address, nonce=1
                    ),
                    2: compute_create_address(
                        address=creator_address, nonce=2
                    ),
                    10: compute_create_address(
                        address=creator_address, nonce=10
                    ),
                }
            ),
        }
    )
    tx = Transaction(
        sender=sender,
        to=contract_address,
        gas_limit=500_000,
    )
    fork = get_deployed_forks()[-1]

    state_test = StateTest(
        pre=pre,
        post=post,
        tx=tx,
        fork=fork,
    )
    state_test.generate(t8n=default_t8n, fixture_format=StateFixture)


@pytest.mark.parametrize(
    "offset,factory_address",
    [
        pytest.param(0, None, id="zero-offset"),
        pytest.param(1, None, id="one-offset"),
        pytest.param(32, None, id="32-offset"),
        pytest.param(0, 0x2000, id="different-factory-address"),
    ],
)
def test_create2_preimage(
    default_t8n: TransitionTool,
    offset: int,
    factory_address: int | None,
) -> None:
    """Test `Create2PreimageLayout` by running its result in the EVM."""
    sender = EOA(key=1)

    contract_address = 0x1000
    factory_address = (
        contract_address if factory_address is None else factory_address
    )
    initcode = Op.STOP
    init_code_hash = initcode.keccak256()
    salt = 1
    address_mask = (1 << 160) - 1

    create2_preimage = Create2PreimageLayout(
        factory_address=Op.ADDRESS
        if factory_address == contract_address
        else factory_address,
        salt=salt,
        init_code_hash=init_code_hash,
        offset=offset,
    )
    contract: Bytecode = (
        create2_preimage
        + Op.SSTORE(1, Op.AND(address_mask, create2_preimage.address_op()))
        + create2_preimage.increment_salt_op()
        + Op.SSTORE(2, Op.AND(address_mask, create2_preimage.address_op()))
        + create2_preimage.increment_salt_op()
        + Op.SSTORE(3, Op.AND(address_mask, create2_preimage.address_op()))
    )

    pre = Alloc(
        {
            sender: Account(balance=(10**18)),
            Address(contract_address): Account(code=contract),
        }
    )
    post = Alloc(
        {
            Address(contract_address): Account(
                storage={
                    1: compute_create2_address(
                        address=factory_address,
                        salt=salt,
                        initcode=initcode,
                    ),
                    2: compute_create2_address(
                        address=factory_address,
                        salt=salt + 1,
                        initcode=initcode,
                    ),
                    3: compute_create2_address(
                        address=factory_address,
                        salt=salt + 2,
                        initcode=initcode,
                    ),
                }
            ),
        }
    )
    tx = Transaction(
        sender=sender,
        to=contract_address,
        gas_limit=500_000,
    )
    fork = get_deployed_forks()[-1]

    state_test = StateTest(
        pre=pre,
        post=post,
        tx=tx,
        fork=fork,
    )
    state_test.generate(t8n=default_t8n, fixture_format=StateFixture)
