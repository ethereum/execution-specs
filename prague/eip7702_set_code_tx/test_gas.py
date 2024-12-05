"""
abstract: Tests related to gas of set-code transactions from [EIP-7702: Set EOA account code for one transaction](https://eips.ethereum.org/EIPS/eip-7702)
    Tests related to gas of set-code transactions from [EIP-7702: Set EOA account code for one transaction](https://eips.ethereum.org/EIPS/eip-7702).
"""  # noqa: E501

from dataclasses import dataclass
from enum import Enum, auto
from itertools import cycle
from typing import Dict, Generator, Iterator, List

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    EOA,
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Bytecode,
    Bytes,
    CodeGasMeasure,
    Environment,
)
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import (
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    extend_with_defaults,
)

from .helpers import AddressType, ChainIDType
from .spec import Spec, ref_spec_7702

REFERENCE_SPEC_GIT_PATH = ref_spec_7702.git_path
REFERENCE_SPEC_VERSION = ref_spec_7702.version

pytestmark = pytest.mark.valid_from("Prague")

# Enum classes used to parametrize the tests


class SignerType(Enum):
    """
    Different cases of authorization lists for testing gas cost of set-code transactions.
    """

    SINGLE_SIGNER = auto()
    MULTIPLE_SIGNERS = auto()


class AuthorizationInvalidityType(Enum):
    """
    Different types of invalidity for the authorization list.
    """

    INVALID_NONCE = auto()
    REPEATED_NONCE = auto()
    INVALID_CHAIN_ID = auto()
    AUTHORITY_IS_CONTRACT = auto()


class AccessListType(Enum):
    """
    Different cases of access lists for testing gas cost of set-code transactions.
    """

    EMPTY = auto()
    CONTAINS_AUTHORITY = auto()
    CONTAINS_SET_CODE_ADDRESS = auto()
    CONTAINS_AUTHORITY_AND_SET_CODE_ADDRESS = auto()

    def contains_authority(self) -> bool:
        """
        Return True if the access list contains the authority address.
        """
        return self in {
            AccessListType.CONTAINS_AUTHORITY,
            AccessListType.CONTAINS_AUTHORITY_AND_SET_CODE_ADDRESS,
        }

    def contains_set_code_address(self) -> bool:
        """
        Return True if the access list contains the address to which the authority authorizes to
        set the code to.
        """
        return self in {
            AccessListType.CONTAINS_SET_CODE_ADDRESS,
            AccessListType.CONTAINS_AUTHORITY_AND_SET_CODE_ADDRESS,
        }


# Fixtures used to parametrize the tests


@dataclass(kw_only=True)
class AuthorityWithProperties:
    """
    Dataclass to hold the properties of the authority address.
    """

    authority: EOA
    address_type: AddressType
    invalidity_type: AuthorizationInvalidityType | None
    empty: bool


@pytest.fixture()
def authority_iterator(
    pre: Alloc,
    sender: EOA,
    authority_type: AddressType | List[AddressType],
    authorize_to_address: Address,
    self_sponsored: bool,
) -> Iterator[AuthorityWithProperties]:
    """
    Fixture to return the generator for the authority addresses.
    """
    authority_type_iterator = (
        cycle([authority_type])
        if isinstance(authority_type, AddressType)
        else cycle(authority_type)
    )

    def generator(
        authority_type_iterator: Iterator[AddressType],
    ) -> Generator[AuthorityWithProperties, None, None]:
        for i, current_authority_type in enumerate(authority_type_iterator):
            match current_authority_type:
                case AddressType.EMPTY_ACCOUNT:
                    assert (
                        not self_sponsored
                    ), "Self-sponsored empty-account authority is not supported"
                    yield AuthorityWithProperties(
                        authority=pre.fund_eoa(0),
                        address_type=current_authority_type,
                        invalidity_type=None,
                        empty=True,
                    )
                case AddressType.EOA:
                    if i == 0 and self_sponsored:
                        yield AuthorityWithProperties(
                            authority=sender,
                            address_type=current_authority_type,
                            invalidity_type=None,
                            empty=False,
                        )
                    else:
                        yield AuthorityWithProperties(
                            authority=pre.fund_eoa(),
                            address_type=current_authority_type,
                            invalidity_type=None,
                            empty=False,
                        )
                case AddressType.EOA_WITH_SET_CODE:
                    if i == 0 and self_sponsored:
                        yield AuthorityWithProperties(
                            authority=sender,
                            address_type=current_authority_type,
                            invalidity_type=None,
                            empty=False,
                        )
                    else:
                        yield AuthorityWithProperties(
                            authority=pre.fund_eoa(0, delegation=authorize_to_address),
                            address_type=current_authority_type,
                            invalidity_type=None,
                            empty=False,
                        )
                case AddressType.CONTRACT:
                    assert (
                        not self_sponsored or i > 0
                    ), "Self-sponsored contract authority is not supported"
                    authority = pre.fund_eoa()
                    authority_account = pre[authority]
                    assert authority_account is not None
                    authority_account.code = Bytes(Op.STOP)
                    yield AuthorityWithProperties(
                        authority=authority,
                        address_type=current_authority_type,
                        invalidity_type=AuthorizationInvalidityType.AUTHORITY_IS_CONTRACT,
                        empty=False,
                    )
                case _:
                    raise ValueError(f"Unsupported authority type: {current_authority_type}")

    return generator(authority_type_iterator)


@dataclass(kw_only=True)
class AuthorizationWithProperties:
    """
    Dataclass to hold the properties of the authorization list.
    """

    tuple: AuthorizationTuple
    invalidity_type: AuthorizationInvalidityType | None
    empty: bool
    skip: bool


@pytest.fixture
def authorization_list_with_properties(
    signer_type: SignerType,
    authorization_invalidity_type: AuthorizationInvalidityType | None,
    authorizations_count: int,
    chain_id_type: ChainIDType,
    authority_iterator: Iterator[AuthorityWithProperties],
    authorize_to_address: Address,
    self_sponsored: bool,
    re_authorize: bool,
) -> List[AuthorizationWithProperties]:
    """
    Fixture to return the authorization-list-with-properties for the given case.
    """
    chain_id = 0 if chain_id_type == ChainIDType.GENERIC else 1
    if authorization_invalidity_type == AuthorizationInvalidityType.INVALID_CHAIN_ID:
        chain_id = 2

    authorization_list: List[AuthorizationWithProperties] = []
    match signer_type:
        case SignerType.SINGLE_SIGNER:
            authority_with_properties = next(authority_iterator)
            # We have to take into account the cases where the nonce has already been increased
            # before the authorization is processed.
            increased_nonce = (
                self_sponsored
                or authority_with_properties.address_type == AddressType.EOA_WITH_SET_CODE
            )
            for i in range(authorizations_count):
                # Get the nonce of this authorization
                match authorization_invalidity_type:
                    case AuthorizationInvalidityType.INVALID_NONCE:
                        nonce = 0 if increased_nonce else 1
                    case AuthorizationInvalidityType.REPEATED_NONCE:
                        nonce = 1 if increased_nonce else 0
                    case _:
                        nonce = i if not increased_nonce else i + 1

                # Get the validity of this authorization
                invalidity_type: AuthorizationInvalidityType | None
                if authorization_invalidity_type is None or (
                    authorization_invalidity_type == AuthorizationInvalidityType.REPEATED_NONCE
                    and i == 0
                ):
                    invalidity_type = authority_with_properties.invalidity_type
                else:
                    invalidity_type = authorization_invalidity_type
                skip = False
                if (
                    authority_with_properties.address_type == AddressType.EOA_WITH_SET_CODE
                    and not re_authorize
                ):
                    skip = True
                authorization_list.append(
                    AuthorizationWithProperties(
                        tuple=AuthorizationTuple(
                            chain_id=chain_id,
                            address=authorize_to_address,
                            nonce=nonce,
                            signer=authority_with_properties.authority,
                        ),
                        invalidity_type=invalidity_type,
                        empty=authority_with_properties.empty,
                        skip=skip,
                    )
                )
            return authorization_list

        case SignerType.MULTIPLE_SIGNERS:
            if authorization_invalidity_type == AuthorizationInvalidityType.REPEATED_NONCE:
                # Reuse the first two authorities for the repeated nonce case
                authority_iterator = cycle([next(authority_iterator), next(authority_iterator)])

            for i in range(authorizations_count):
                # Get the nonce of this authorization
                authority_with_properties = next(authority_iterator)
                increased_nonce = (
                    self_sponsored and i == 0
                ) or authority_with_properties.address_type == AddressType.EOA_WITH_SET_CODE
                if increased_nonce:
                    if authorization_invalidity_type == AuthorizationInvalidityType.INVALID_NONCE:
                        nonce = 0
                    else:
                        nonce = 1
                else:
                    if authorization_invalidity_type == AuthorizationInvalidityType.INVALID_NONCE:
                        nonce = 1
                    else:
                        nonce = 0

                # Get the validity of this authorization
                if authorization_invalidity_type is None or (
                    authorization_invalidity_type == AuthorizationInvalidityType.REPEATED_NONCE
                    and i <= 1
                ):
                    invalidity_type = authority_with_properties.invalidity_type
                else:
                    invalidity_type = authorization_invalidity_type
                skip = False
                if (
                    authority_with_properties.address_type == AddressType.EOA_WITH_SET_CODE
                    and not re_authorize
                ):
                    skip = True
                authorization_list.append(
                    AuthorizationWithProperties(
                        tuple=AuthorizationTuple(
                            chain_id=chain_id,
                            address=authorize_to_address,
                            nonce=nonce,
                            signer=authority_with_properties.authority,
                        ),
                        invalidity_type=invalidity_type,
                        empty=authority_with_properties.empty,
                        skip=skip,
                    )
                )
            return authorization_list
        case _:
            raise ValueError(f"Unsupported authorization list case: {signer_type}")


@pytest.fixture
def authorization_list(
    authorization_list_with_properties: List[AuthorizationWithProperties],
) -> List[AuthorizationTuple]:
    """
    Fixture to return the authorization list for the given case.
    """
    return [
        authorization_tuple.tuple
        for authorization_tuple in authorization_list_with_properties
        if not authorization_tuple.skip
    ]


@pytest.fixture()
def authorize_to_address(request: pytest.FixtureRequest, pre: Alloc) -> Address:
    """
    Fixture to return the address to which the authority authorizes to set the code to.
    """
    match request.param:
        case AddressType.EMPTY_ACCOUNT:
            return pre.fund_eoa(0)
        case AddressType.EOA:
            return pre.fund_eoa(1)
        case AddressType.CONTRACT:
            return pre.deploy_contract(Op.STOP)
    raise ValueError(f"Unsupported authorization address case: {request.param}")


@pytest.fixture()
def access_list(
    access_list_case: AccessListType,
    authorization_list: List[AuthorizationTuple],
) -> List[AccessList]:
    """
    Fixture to return the access list for the given case.
    """
    access_list: List[AccessList] = []
    if access_list_case == AccessListType.EMPTY:
        return access_list

    if access_list_case.contains_authority():
        authority_set = set(a.signer for a in authorization_list)
        access_list.extend(
            AccessList(address=authority, storage_keys=[0]) for authority in authority_set
        )

    if access_list_case.contains_set_code_address():
        authorized_addresses = set(a.address for a in authorization_list)
        access_list.extend(
            AccessList(address=address, storage_keys=[0]) for address in authorized_addresses
        )

    return access_list


@pytest.fixture()
def sender(
    pre: Alloc,
    authority_type: AddressType | List[AddressType],
    authorize_to_address: Address,
    self_sponsored: bool,
) -> EOA:
    """
    Fixture to return the sender address.
    """
    if self_sponsored and (
        (isinstance(authority_type, list) and AddressType.EOA_WITH_SET_CODE in authority_type)
        or (authority_type == AddressType.EOA_WITH_SET_CODE)
    ):
        return pre.fund_eoa(delegation=authorize_to_address)
    return pre.fund_eoa()


# Helper functions to parametrize the tests


def gas_test_parameter_args(
    include_many: bool = True, include_data: bool = True, include_pre_authorized: bool = True
):
    """
    Return the parametrize decorator that can be used in all gas test functions.
    """
    MULTIPLE_AUTHORIZATIONS_COUNT = 2
    MANY_AUTHORIZATIONS_COUNT = 5_000

    defaults = dict(
        signer_type=SignerType.SINGLE_SIGNER,
        authorization_invalidity_type=None,
        authorizations_count=1,
        chain_id_type=ChainIDType.GENERIC,
        authorize_to_address=AddressType.EMPTY_ACCOUNT,
        access_list_case=AccessListType.EMPTY,
        self_sponsored=False,
        re_authorize=False,
        authority_type=AddressType.EMPTY_ACCOUNT,
        data=b"",
    )

    cases = [
        pytest.param(
            dict(
                signer_type=SignerType.SINGLE_SIGNER,
                authorizations_count=1,
            ),
            id="single_valid_authorization_single_signer",
        ),
        pytest.param(
            dict(
                signer_type=SignerType.SINGLE_SIGNER,
                authorizations_count=1,
                chain_id_type=ChainIDType.CHAIN_SPECIFIC,
            ),
            id="single_valid_chain_specific_authorization_single_signer",
        ),
        pytest.param(
            dict(
                signer_type=SignerType.SINGLE_SIGNER,
                authorizations_count=MULTIPLE_AUTHORIZATIONS_COUNT,
            ),
            id="multiple_valid_authorizations_single_signer",
        ),
        pytest.param(
            dict(
                signer_type=SignerType.SINGLE_SIGNER,
                authorization_invalidity_type=AuthorizationInvalidityType.INVALID_NONCE,
                authorizations_count=1,
            ),
            id="single_invalid_nonce_authorization_single_signer",
        ),
        pytest.param(
            dict(
                signer_type=SignerType.SINGLE_SIGNER,
                authorization_invalidity_type=AuthorizationInvalidityType.INVALID_CHAIN_ID,
                authorizations_count=1,
            ),
            id="single_invalid_authorization_invalid_chain_id_single_signer",
        ),
        pytest.param(
            dict(
                signer_type=SignerType.SINGLE_SIGNER,
                authorization_invalidity_type=AuthorizationInvalidityType.INVALID_NONCE,
                authorizations_count=MULTIPLE_AUTHORIZATIONS_COUNT,
            ),
            id="multiple_invalid_nonce_authorizations_single_signer",
        ),
        pytest.param(
            dict(
                signer_type=SignerType.MULTIPLE_SIGNERS,
                authorization_invalidity_type=AuthorizationInvalidityType.INVALID_NONCE,
                authorizations_count=MULTIPLE_AUTHORIZATIONS_COUNT,
            ),
            id="multiple_invalid_nonce_authorizations_multiple_signers",
        ),
        pytest.param(
            dict(
                signer_type=SignerType.SINGLE_SIGNER,
                authorization_invalidity_type=AuthorizationInvalidityType.INVALID_CHAIN_ID,
                authorizations_count=MULTIPLE_AUTHORIZATIONS_COUNT,
            ),
            id="multiple_invalid_chain_id_authorizations_single_signer",
        ),
        pytest.param(
            dict(
                signer_type=SignerType.MULTIPLE_SIGNERS,
                authorizations_count=MULTIPLE_AUTHORIZATIONS_COUNT,
            ),
            id="multiple_valid_authorizations_multiple_signers",
        ),
        pytest.param(
            dict(
                signer_type=SignerType.SINGLE_SIGNER,
                authorization_invalidity_type=AuthorizationInvalidityType.REPEATED_NONCE,
                authorizations_count=MULTIPLE_AUTHORIZATIONS_COUNT,
            ),
            id="first_valid_then_single_repeated_nonce_authorization",
        ),
        pytest.param(
            dict(
                signer_type=SignerType.MULTIPLE_SIGNERS,
                authorization_invalidity_type=AuthorizationInvalidityType.REPEATED_NONCE,
                authorizations_count=MULTIPLE_AUTHORIZATIONS_COUNT * 2,
            ),
            id="first_valid_then_single_repeated_nonce_authorizations_multiple_signers",
        ),
        pytest.param(
            dict(
                authorize_to_address=AddressType.EOA,
            ),
            id="single_valid_authorization_to_eoa",
        ),
        pytest.param(
            dict(
                authorize_to_address=AddressType.CONTRACT,
            ),
            id="single_valid_authorization_to_contract",
        ),
        pytest.param(
            dict(
                access_list_case=AccessListType.CONTAINS_AUTHORITY,
            ),
            id="single_valid_authorization_with_authority_in_access_list",
        ),
        pytest.param(
            dict(
                access_list_case=AccessListType.CONTAINS_SET_CODE_ADDRESS,
            ),
            id="single_valid_authorization_with_set_code_address_in_access_list",
        ),
        pytest.param(
            dict(
                access_list_case=AccessListType.CONTAINS_AUTHORITY_AND_SET_CODE_ADDRESS,
            ),
            id="single_valid_authorization_with_authority_and_set_code_address_in_access_list",
        ),
        pytest.param(
            dict(
                authority_type=AddressType.EOA,
            ),
            id="single_valid_authorization_eoa_authority",
        ),
        pytest.param(
            dict(
                authority_type=AddressType.EOA_WITH_SET_CODE,
                re_authorize=True,
            ),
            id="single_valid_re_authorization_eoa_authority",
        ),
        pytest.param(
            dict(
                authority_type=AddressType.EOA,
                authorizations_count=MULTIPLE_AUTHORIZATIONS_COUNT,
            ),
            id="multiple_valid_authorizations_eoa_authority",
        ),
        pytest.param(
            dict(
                self_sponsored=True,
                authority_type=AddressType.EOA,
            ),
            id="single_valid_authorization_eoa_self_sponsored_authority",
        ),
        pytest.param(
            dict(
                self_sponsored=True,
                authority_type=AddressType.EOA,
                authorizations_count=MULTIPLE_AUTHORIZATIONS_COUNT,
            ),
            id="multiple_valid_authorizations_eoa_self_sponsored_authority",
        ),
        pytest.param(
            dict(
                authority_type=AddressType.CONTRACT,
            ),
            marks=pytest.mark.pre_alloc_modify,
            id="single_valid_authorization_invalid_contract_authority",
        ),
        pytest.param(
            dict(
                signer_type=SignerType.MULTIPLE_SIGNERS,
                authority_type=[AddressType.EMPTY_ACCOUNT, AddressType.CONTRACT],
                authorizations_count=MULTIPLE_AUTHORIZATIONS_COUNT,
            ),
            marks=pytest.mark.pre_alloc_modify,
            id="multiple_authorizations_empty_account_then_contract_authority",
        ),
        pytest.param(
            dict(
                signer_type=SignerType.MULTIPLE_SIGNERS,
                authority_type=[AddressType.EOA, AddressType.CONTRACT],
                authorizations_count=MULTIPLE_AUTHORIZATIONS_COUNT,
            ),
            marks=pytest.mark.pre_alloc_modify,
            id="multiple_authorizations_eoa_then_contract_authority",
        ),
        pytest.param(
            dict(
                self_sponsored=True,
                signer_type=SignerType.MULTIPLE_SIGNERS,
                authority_type=[AddressType.EOA, AddressType.CONTRACT],
                authorizations_count=MULTIPLE_AUTHORIZATIONS_COUNT,
            ),
            marks=pytest.mark.pre_alloc_modify,
            id="multiple_authorizations_eoa_self_sponsored_then_contract_authority",
        ),
    ]

    if include_pre_authorized:
        cases += [
            pytest.param(
                dict(
                    authority_type=AddressType.EOA_WITH_SET_CODE,
                    re_authorize=False,
                ),
                id="pre_authorized_eoa_authority_no_re_authorization",
            ),
            pytest.param(
                dict(
                    authority_type=AddressType.EOA_WITH_SET_CODE,
                    re_authorize=False,
                    self_sponsored=True,
                ),
                id="pre_authorized_eoa_authority_no_re_authorization_self_sponsored",
            ),
        ]

    if include_data:
        cases += [
            pytest.param(
                dict(
                    data=b"\x01",
                ),
                id="single_valid_authorization_with_single_non_zero_byte_data",
            ),
            pytest.param(
                dict(
                    data=b"\x00",
                ),
                id="single_valid_authorization_with_single_zero_byte_data",
            ),
        ]

    if include_many:
        cases += [
            pytest.param(
                dict(
                    signer_type=SignerType.SINGLE_SIGNER,
                    authorizations_count=MANY_AUTHORIZATIONS_COUNT,
                ),
                id="many_valid_authorizations_single_signer",
            ),
            pytest.param(
                dict(
                    signer_type=SignerType.MULTIPLE_SIGNERS,
                    authorizations_count=MANY_AUTHORIZATIONS_COUNT,
                ),
                id="many_valid_authorizations_multiple_signers",
            ),
            pytest.param(
                dict(
                    signer_type=SignerType.SINGLE_SIGNER,
                    authorization_invalidity_type=AuthorizationInvalidityType.REPEATED_NONCE,
                    authorizations_count=MANY_AUTHORIZATIONS_COUNT,
                ),
                id="first_valid_then_many_duplicate_authorizations",
            ),
        ]
    return extend_with_defaults(cases=cases, defaults=defaults, indirect=["authorize_to_address"])


# Tests


@pytest.mark.parametrize(**gas_test_parameter_args(include_pre_authorized=False))
def test_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    authorization_list_with_properties: List[AuthorizationWithProperties],
    authorization_list: List[AuthorizationTuple],
    data: bytes,
    access_list: List[AccessList],
    sender: EOA,
):
    """
    Test gas at the execution start of a set-code transaction in multiple scenarios.
    """
    # Calculate the intrinsic gas cost of the authorizations, by default the
    # full empty account cost is charged for each authorization.
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=data,
        access_list=access_list,
        authorization_list_or_count=authorization_list,
    )

    discounted_authorizations = 0
    seen_authority = set()
    for authorization_with_properties in authorization_list_with_properties:
        if authorization_with_properties.invalidity_type is None:
            authority = authorization_with_properties.tuple.signer
            if not authorization_with_properties.empty:
                seen_authority.add(authority)
            if authority in seen_authority:
                discounted_authorizations += 1
            else:
                seen_authority.add(authority)

    discount_gas = (
        Spec.PER_EMPTY_ACCOUNT_COST - Spec.PER_AUTH_BASE_COST
    ) * discounted_authorizations

    # We calculate the exact gas required to execute the test code.
    # We add SSTORE opcodes in order to make sure that the refund is less than one fifth (EIP-3529)
    # of the total gas used, so we can see the full discount being reflected in most of the tests.
    gas_opcode_cost = 2
    sstore_opcode_count = 10
    push_opcode_count = (2 * (sstore_opcode_count)) - 1
    push_opcode_cost = 3 * push_opcode_count
    sstore_opcode_cost = 20_000 * sstore_opcode_count
    cold_storage_cost = 2_100 * sstore_opcode_count

    execution_gas = gas_opcode_cost + push_opcode_cost + sstore_opcode_cost + cold_storage_cost

    # The first opcode that executes in the code is the GAS opcode, which costs 2 gas, so we
    # subtract that from the expected gas measure.
    expected_gas_measure = execution_gas - gas_opcode_cost

    test_code_storage = Storage()
    test_code = (
        Op.SSTORE(test_code_storage.store_next(expected_gas_measure), Op.GAS)
        + sum(
            Op.SSTORE(test_code_storage.store_next(1), 1) for _ in range(sstore_opcode_count - 1)
        )
        + Op.STOP
    )
    test_code_address = pre.deploy_contract(test_code)

    tx_gas_limit = intrinsic_gas + execution_gas
    tx_max_fee_per_gas = 7
    tx_exact_cost = tx_gas_limit * tx_max_fee_per_gas

    # EIP-3529
    max_discount = tx_gas_limit // 5

    if discount_gas > max_discount:
        # Only one test hits this condition, but it's ok to also test this case.
        discount_gas = max_discount

    discount_cost = discount_gas * tx_max_fee_per_gas

    sender_account = pre[sender]
    assert sender_account is not None

    tx = Transaction(
        gas_limit=tx_gas_limit,
        max_fee_per_gas=tx_max_fee_per_gas,
        to=test_code_address,
        value=0,
        data=data,
        authorization_list=authorization_list,
        access_list=access_list,
        sender=sender,
    )

    state_test(
        env=Environment(gas_limit=max(tx_gas_limit, 30_000_000)),
        pre=pre,
        tx=tx,
        post={
            test_code_address: Account(storage=test_code_storage),
            sender: Account(balance=sender_account.balance - tx_exact_cost + discount_cost),
        },
    )


@pytest.mark.parametrize("check_delegated_account_first", [True, False])
@pytest.mark.parametrize(**gas_test_parameter_args(include_many=False, include_data=False))
def test_account_warming(
    state_test: StateTestFiller,
    pre: Alloc,
    authorization_list_with_properties: List[AuthorizationWithProperties],
    authorization_list: List[AuthorizationTuple],
    access_list_case: AccessListType,
    access_list: List[AccessList],
    data: bytes,
    sender: EOA,
    check_delegated_account_first: bool,
):
    """
    Test warming of the authority and authorized accounts for set-code transactions.
    """
    # Overhead cost is the single push operation required for the address to check.
    OVERHEAD_COST = 3 * len(Op.CALL.kwargs)  # type: ignore

    COLD_ACCOUNT_COST = 2600
    WARM_ACCOUNT_COST = 100

    # Dictionary to keep track of the addresses to check for warming, and the expected cost of
    # accessing such account.
    addresses_to_check: Dict[Address, int] = {}

    for authorization_with_properties in authorization_list_with_properties:
        authority = authorization_with_properties.tuple.signer
        assert authority is not None, "authority address is not set"
        delegated_account = authorization_with_properties.tuple.address

        if check_delegated_account_first:
            if delegated_account not in addresses_to_check:
                addresses_to_check[delegated_account] = (
                    WARM_ACCOUNT_COST
                    if access_list_case.contains_set_code_address()
                    else COLD_ACCOUNT_COST
                )

            if authority not in addresses_to_check:
                if not authorization_with_properties.skip:
                    if (
                        authorization_with_properties.invalidity_type is None
                        or (
                            authorization_with_properties.invalidity_type
                            != AuthorizationInvalidityType.INVALID_CHAIN_ID
                        )
                        or access_list_case.contains_authority()
                    ):
                        access_cost = WARM_ACCOUNT_COST
                    else:
                        access_cost = COLD_ACCOUNT_COST
                    if authorization_with_properties.invalidity_type is None:
                        access_cost += WARM_ACCOUNT_COST
                else:
                    access_cost = (
                        COLD_ACCOUNT_COST
                        if Address(sender) != authorization_with_properties.tuple.signer
                        else WARM_ACCOUNT_COST
                    )
                    if authorization_with_properties.invalidity_type is None:
                        access_cost += WARM_ACCOUNT_COST

                addresses_to_check[authority] = access_cost

        else:
            if authority not in addresses_to_check:
                access_cost = (
                    COLD_ACCOUNT_COST
                    if Address(sender) != authorization_with_properties.tuple.signer
                    else WARM_ACCOUNT_COST
                )
                if not authorization_with_properties.skip and (
                    authorization_with_properties.invalidity_type is None
                    or (
                        authorization_with_properties.invalidity_type
                        != AuthorizationInvalidityType.INVALID_CHAIN_ID
                    )
                    or access_list_case.contains_authority()
                ):
                    access_cost = WARM_ACCOUNT_COST

                if (
                    # We can only charge the delegated account access cost if the authorization
                    # went through
                    authorization_with_properties.invalidity_type
                    is None
                ):
                    if (
                        delegated_account in addresses_to_check
                        or access_list_case.contains_set_code_address()
                    ):
                        access_cost += WARM_ACCOUNT_COST
                    else:
                        access_cost += COLD_ACCOUNT_COST

                addresses_to_check[authority] = access_cost

            if delegated_account not in addresses_to_check:
                if (
                    authorization_with_properties.invalidity_type is None
                    or access_list_case.contains_set_code_address()
                ):
                    access_cost = WARM_ACCOUNT_COST
                else:
                    access_cost = COLD_ACCOUNT_COST
                addresses_to_check[delegated_account] = access_cost

    callee_storage = Storage()
    callee_code: Bytecode = sum(  # type: ignore
        (
            CodeGasMeasure(
                code=Op.CALL(gas=0, address=check_address),
                overhead_cost=OVERHEAD_COST,
                extra_stack_items=1,
                sstore_key=callee_storage.store_next(access_cost),
                stop=False,
            )
            for check_address, access_cost in addresses_to_check.items()
        )
    )
    callee_code += Op.STOP
    callee_address = pre.deploy_contract(callee_code, storage=callee_storage.canary())

    tx = Transaction(
        gas_limit=1_000_000,
        to=callee_address,
        authorization_list=authorization_list if authorization_list else None,
        access_list=access_list,
        sender=sender,
        data=data,
    )
    post = {
        callee_address: Account(
            storage=callee_storage,
        ),
    }

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )


@pytest.mark.parametrize(**gas_test_parameter_args(include_pre_authorized=False))
@pytest.mark.parametrize(
    "valid",
    [True, False],
)
def test_intrinsic_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    authorization_list: List[AuthorizationTuple],
    data: bytes,
    access_list: List[AccessList],
    sender: EOA,
    valid: bool,
):
    """
    Test sending a transaction with the exact intrinsic gas required and also insufficient
    gas.
    """
    # Calculate the intrinsic gas cost of the authorizations, by default the
    # full empty account cost is charged for each authorization.
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=data,
        access_list=access_list,
        authorization_list_or_count=authorization_list,
    )

    tx_gas = intrinsic_gas
    if not valid:
        tx_gas -= 1

    test_code = Op.STOP
    test_code_address = pre.deploy_contract(test_code)

    tx = Transaction(
        gas_limit=tx_gas,
        to=test_code_address,
        value=0,
        data=data,
        authorization_list=authorization_list,
        access_list=access_list,
        sender=sender,
        error=TransactionException.INTRINSIC_GAS_TOO_LOW if not valid else None,
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={},
    )


@pytest.mark.parametrize("pre_authorized", [True, False])
def test_self_set_code_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    pre_authorized: bool,
):
    """
    Test set to code account access cost when it delegates to itself.
    """
    if pre_authorized:
        auth_signer = pre.fund_eoa(0, delegation="Self")
    else:
        auth_signer = pre.fund_eoa(0)

    slot_call_cost = 1

    OVERHEAD_COST = 3 * len(Op.CALL.kwargs)  # type: ignore

    callee_code = CodeGasMeasure(
        code=Op.CALL(gas=0, address=auth_signer),
        overhead_cost=OVERHEAD_COST,
        extra_stack_items=1,
        sstore_key=slot_call_cost,
    )

    callee_address = pre.deploy_contract(callee_code)
    callee_storage = Storage()
    callee_storage[slot_call_cost] = 200 if not pre_authorized else 2700

    tx = Transaction(
        gas_limit=1_000_000,
        to=callee_address,
        authorization_list=[
            AuthorizationTuple(
                address=auth_signer,
                nonce=0,
                signer=auth_signer,
            ),
        ]
        if not pre_authorized
        else None,
        sender=pre.fund_eoa(),
    )

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post={
            callee_address: Account(storage=callee_storage),
            auth_signer: Account(
                nonce=1,
                code=Spec.delegation_designation(auth_signer),
            ),
        },
    )
