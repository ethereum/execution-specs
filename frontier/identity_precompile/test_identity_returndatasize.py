"""abstract: Test identity precompile output size."""

import pytest

from ethereum_test_base_types.composite_types import Storage
from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op
from tests.frontier.identity_precompile.common import Constants


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts/identity_to_biggerFiller.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts/identity_to_smallerFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-spec-tests/pull/1344"],
)
@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    ["args_size", "output_size", "expected_returndatasize"],
    [
        pytest.param(16, 32, 16, id="output_size_greater_than_input"),
        pytest.param(32, 16, 32, id="output_size_less_than_input"),
    ],
)
def test_identity_precompile_returndata(
    state_test: StateTestFiller,
    pre: Alloc,
    args_size: int,
    output_size: int,
    expected_returndatasize: int,
):
    """Test identity precompile RETURNDATA is sized correctly based on the input size."""
    env = Environment()
    storage = Storage()

    account = pre.deploy_contract(
        Op.MSTORE(0, 0)
        + Op.GAS
        + Op.MSTORE(0, 0x112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00)
        + Op.POP(
            Op.CALL(
                address=Constants.IDENTITY_PRECOMPILE_ADDRESS,
                args_offset=0,
                args_size=args_size,
                output_offset=0x10,
                output_size=output_size,
            )
        )
        + Op.SSTORE(storage.store_next(expected_returndatasize), Op.RETURNDATASIZE)
        + Op.STOP,
        storage=storage.canary(),
    )

    tx = Transaction(
        to=account,
        sender=pre.fund_eoa(),
        gas_limit=200_000,
        protected=True,
    )

    post = {account: Account(storage=storage)}

    state_test(env=env, pre=pre, post=post, tx=tx)
