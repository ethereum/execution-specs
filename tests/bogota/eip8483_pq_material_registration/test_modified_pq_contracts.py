"""
Tests of blocks whose registration predeploys have other code, for
[EIP-8483: Post-Quantum Material Registration](https://eips.ethereum.org/EIPS/eip-8483).
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    BlockException,
    Bytecode,
    EIPChecklist,
    FeeSystemContractRequest,
    Header,
    Op,
    PQBuilderRegistrationRequest,
    PQRegistrationRequest,
    Requests,
    generate_system_contract_error_test,
)

from .helpers import with_both_registrations
from .spec import ref_spec_8483

REFERENCE_SPEC_GIT_PATH = ref_spec_8483.git_path
REFERENCE_SPEC_VERSION = ref_spec_8483.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.pre_alloc_mutable,
]

# Records from a source that never registers in these tests.
RECORD_SOURCE = Address(0x5EED)


def returning(data: bytes) -> Bytecode:
    """Return code that returns `data`, which it carries after its code."""
    size = Op.PUSH3[len(data)]
    header_size = len(Op.CODECOPY(0, Op.PUSH3[0], size) + Op.RETURN(0, size))
    return (
        Op.CODECOPY(0, Op.PUSH3[header_size], size) + Op.RETURN(0, size) + data
    )


@pytest.mark.parametrize(
    "system_contract",
    [
        pytest.param(
            PQRegistrationRequest.system_contract_address, id="validator"
        ),
        pytest.param(
            PQBuilderRegistrationRequest.system_contract_address,
            id="builder",
        ),
    ],
)
@EIPChecklist.SystemContract.Test.ContractSubstitution.RaisesException()
@EIPChecklist.SystemContract.Test.ContractSubstitution.GasLimitSuccess()
@EIPChecklist.SystemContract.Test.ContractSubstitution.GasLimitFailure()
@EIPChecklist.SystemContract.Test.ExcessiveGas.SystemCall()
@generate_system_contract_error_test()  # type: ignore[arg-type]
def test_system_contract_errors() -> None:
    """
    A registration predeploy that runs out of gas, reverts or throws in the
    system call makes the block invalid, and one that uses up to the system
    call's gas limit doesn't.

    See `generate_system_contract_error_test` for the generated cases.
    """
    pass


@pytest.mark.exception_test
@with_both_registrations
@EIPChecklist.SystemContract.Test.Deployment.Missing()
def test_predeploy_without_code(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: type[FeeSystemContractRequest],
) -> None:
    """A block is invalid when a registration predeploy has no code."""
    del pre[request_class.system_contract_address]

    blockchain_test(
        pre=pre,
        blocks=[Block(exception=BlockException.SYSTEM_CONTRACT_EMPTY)],
        post={},
        # Every block calls the predeploy, so no block can follow this one.
        sync_block=False,
    )


@with_both_registrations
@EIPChecklist.SystemContract.Test.ContractSubstitution.ReturnLengths()
def test_more_records_than_max_per_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    request_class: type[FeeSystemContractRequest],
) -> None:
    """
    The block's requests are what the system call returns, even when a
    replaced predeploy returns more records than its per-block maximum.
    """
    records = [
        request_class.from_index(i).with_source_address(RECORD_SOURCE)
        for i in range(request_class.max_per_block + 1)
    ]
    pre[request_class.system_contract_address] = Account(
        code=returning(b"".join(bytes(record) for record in records)),
        nonce=1,
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(header_verify=Header(requests_hash=Requests(*records)))],
        post={},
    )
