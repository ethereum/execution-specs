"""
EOF V1 Code Validation tests
"""

from typing import Dict, List

import pytest

from ethereum_test_tools import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    EOFTestFiller,
    Transaction,
    compute_eofcreate_address,
)
from ethereum_test_tools.eof.v1 import Container, Initcode

from .. import EOF_FORK_NAME

# from .code_validation import INVALID as INVALID_CODE
# from .code_validation import VALID as VALID_CODE
# from .code_validation_function import INVALID as INVALID_FN
# from .code_validation_function import VALID as VALID_FN
# from .code_validation_jump import INVALID as INVALID_RJUMP
# from .code_validation_jump import VALID as VALID_RJUMP
from .container import INVALID as INVALID_CONTAINERS
from .container import VALID as VALID_CONTAINERS

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
def sender(pre: Alloc):  # noqa: D103
    return pre.fund_eoa()


@pytest.fixture
def create3_init_container(container: Container) -> Initcode:  # noqa: D103
    return Initcode(deploy_container=container)


@pytest.fixture
def create3_opcode_contract_address(  # noqa: D103
    pre: Alloc,
    create3_init_container: Initcode,
) -> Address:
    return pre.deploy_contract(create3_init_container, address=Address(0x300))


@pytest.fixture
def txs(  # noqa: D103
    sender: EOA,
    create3_opcode_contract_address: Address,
) -> List[Transaction]:
    return [
        Transaction(
            to=create3_opcode_contract_address,
            gas_limit=100000000,
            gas_price=10,
            # data=initcode,
            protected=False,
            sender=sender,
        )
    ]


@pytest.fixture
def post(  # noqa: D103
    create3_init_container: Initcode,
    container: Container,
    create3_opcode_contract_address: Address,
) -> Dict[Address, Account]:
    create_opcode_created_contract_address = compute_eofcreate_address(
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
