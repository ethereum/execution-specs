"""
EOF V1 Code Validation tests
"""

from typing import Dict, List

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Environment,
    EOFTestFiller,
    TestAddress,
    Transaction,
    compute_create3_address,
)
from ethereum_test_tools.eof.v1 import Container, Initcode

# from .code_validation import INVALID as INVALID_CODE
# from .code_validation import VALID as VALID_CODE
# from .code_validation_function import INVALID as INVALID_FN
# from .code_validation_function import VALID as VALID_FN
# from .code_validation_jump import INVALID as INVALID_RJUMP
# from .code_validation_jump import VALID as VALID_RJUMP
from .container import INVALID as INVALID_CONTAINERS
from .container import VALID as VALID_CONTAINERS
from .spec import EOF_FORK_NAME

# from .tests_execution_function import VALID as VALID_EXEC_FN

ALL_VALID = VALID_CONTAINERS
ALL_INVALID = INVALID_CONTAINERS
# ALL_VALID = (
#     VALID_CONTAINERS + VALID_CODE + VALID_RJUMP + VALID_FN + VALID_EXEC_FN
# )
# ALL_INVALID = INVALID_CONTAINERS + INVALID_CODE + INVALID_RJUMP + INVALID_FN

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "8dcb0a8c1c0102c87224308028632cc986a61183"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.fixture
def env():  # noqa: D103
    return Environment()


@pytest.fixture
def create3_init_container(container: Container) -> Initcode:  # noqa: D103
    return Initcode(deploy_container=container)


@pytest.fixture
def create3_opcode_contract_address() -> Address:  # noqa: D103
    return Address(0x300)


@pytest.fixture
def pre(  # noqa: D103
    create3_opcode_contract_address: Address,
    create3_init_container: Initcode,
) -> Alloc:
    return Alloc(
        {
            TestAddress: Account(
                balance=1000000000000000000000,
                nonce=0,
            ),
            create3_opcode_contract_address: Account(
                code=create3_init_container,
            ),
        }
    )


@pytest.fixture
def txs(  # noqa: D103
    create3_opcode_contract_address: str,
) -> List[Transaction]:
    return [
        Transaction(
            nonce=nonce,
            to=address,
            gas_limit=100000000,
            gas_price=10,
            # data=initcode,
            protected=False,
        )
        for nonce, address in enumerate(
            [
                create3_opcode_contract_address,
            ]
        )
    ]


@pytest.fixture
def post(  # noqa: D103
    create3_init_container: Initcode,
    container: Container,
    create3_opcode_contract_address: str,
) -> Dict[Address, Account]:
    create_opcode_created_contract_address = compute_create3_address(
        create3_opcode_contract_address,
        0,
        bytes(create3_init_container.init_container),
    )

    new_account = Account(code=container)

    # Do not expect to create account if it is invalid
    if hasattr(new_account, "code") and container.validity_error != "":
        return {}
    else:
        return {
            create_opcode_created_contract_address: new_account,
        }


def container_name(c: Container):
    """
    Return the name of the container for use in pytest ids.
    """
    if hasattr(c, "name"):
        return c.name
    else:
        return c.__class__.__name__


@pytest.mark.parametrize(
    "container",
    ALL_VALID,
    ids=container_name,
)
def test_legacy_initcode_valid_eof_v1_contract(
    eof_test: EOFTestFiller,
    container: Container,
):
    """
    Test creating various types of valid EOF V1 contracts using legacy
    initcode and a contract creating transaction.
    """
    assert (
        container.validity_error is None
    ), f"Valid container with validity error: {container.validity_error}"
    eof_test(
        data=bytes(container),
    )


@pytest.mark.parametrize(
    "container",
    ALL_INVALID,
    ids=container_name,
)
def test_legacy_initcode_invalid_eof_v1_contract(
    eof_test: EOFTestFiller,
    container: Container,
):
    """
    Test creating various types of valid EOF V1 contracts using legacy
    initcode and a contract creating transaction.
    """
    assert container.validity_error is not None, "Invalid container without validity error"
    eof_test(
        data=bytes(container),
        expect_exception=container.validity_error,
    )


"""
@test_from(EOF_FORK_NAME)
def test_legacy_initcode_invalid_eof_v1_contract(_):
    Test creating various types of invalid EOF V1 contracts using legacy
    initcode, a contract creating transaction,
    and the CREATE opcode.
    tx_created_contract_address = compute_create_address(TestAddress, 0)
    create_opcode_created_contract_address = compute_create_address(0x100, 0)

    env = Environment()

    pre = {
        TestAddress: Account(
            balance=1000000000000000000000,
            nonce=0,
        ),
        Address(0x100): Account(
            code=create_initcode_from_calldata,
        ),
        Address(0x200): Account(
            code=create2_initcode_from_calldata,
        ),
    }

    post = {
        Address(0x100): Account(
            storage={
                0: 1,
            }
        ),
        tx_created_contract_address: Account.NONEXISTENT,
        create_opcode_created_contract_address: Account.NONEXISTENT,
    }

    tx_create_contract = Transaction(
        nonce=0,
        to=None,
        gas_limit=100000000,
        gas_price=10,
        protected=False,
    )
    tx_create_opcode = Transaction(
        nonce=1,
        to=Address(0x100),
        gas_limit=100000000,
        gas_price=10,
        protected=False,
    )
    tx_create2_opcode = Transaction(
        nonce=2,
        to=Address(0x200),
        gas_limit=100000000,
        gas_price=10,
        protected=False,
    )

    for container in ALL_INVALID:
        # print(container.name + ": " + bytes(container).hex())
        if container.validity_error == "":
            print(
                "WARN: Invalid container "
                + f"`{container.name}` without validity error"
            )
        legacy_initcode = Initcode(deploy_code=container)
        tx_create_contract.data = legacy_initcode
        tx_create_opcode.data = legacy_initcode
        tx_create2_opcode.data = legacy_initcode
        create2_opcode_created_contract_address = compute_create2_address(
            0x200, 0, bytes(legacy_initcode)
        )
        post[create2_opcode_created_contract_address] = Account.NONEXISTENT
        yield StateTest(
            env=env,
            pre=pre,
            post=post,
            txs=[
                tx_create_contract,
                tx_create_opcode,
                tx_create2_opcode,
            ],
            name=container.name
            if container.name is not None
            else "unknown_container",
        )
        del post[create2_opcode_created_contract_address]
    """


# TODO: EOF cannot create legacy code:
#       Tx -> EOF-initcode -> Legacy return (Fail)
#       EOF contract CREATE -> EOF-initcode -> Legacy return (Fail)
#       EOF contract CREATE2 -> EOF-initcode -> Legacy return (Fail)
#
#       Tx -> Legacy-initcode -> Legacy return (Pass)
#       EOF contract CREATE -> Legacy-initcode -> Legacy return (Fail)
#       EOF contract CREATE2 -> Legacy-initcode -> Legacy return (Fail)
#
#       Tx -> Legacy-initcode -> EOF return (Pass)
#       EOF contract CREATE -> Legacy-initcode -> EOF return (Fail)
#       EOF contract CREATE2 -> Legacy-initcode -> EOF return (Fail)
# TODO: Create empty contract from EOF
# TODO: No new opcodes in legacy code
# TODO: General EOF initcode validation
