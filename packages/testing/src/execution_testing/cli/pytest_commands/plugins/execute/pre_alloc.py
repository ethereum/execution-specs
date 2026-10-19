"""Pre-allocation fixtures used for test filling."""

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import count
from pathlib import Path
from random import randint
from typing import Any, Dict, Generator, Iterator, List, Literal, Tuple

import pytest
from filelock import FileLock
from pydantic import PrivateAttr

from execution_testing.base_types import (
    Account,
    Address,
    Bytes,
    Hash,
    HexNumber,
    Number,
    Storage,
    StorageRootType,
)
from execution_testing.base_types.conversions import (
    BytesConvertible,
    NumberConvertible,
)
from execution_testing.forks import Fork, TransitionFork
from execution_testing.logging import get_logger
from execution_testing.recipient_type import RecipientType
from execution_testing.rpc import EthRPC
from execution_testing.rpc.rpc_types import TransactionByHashResponse
from execution_testing.test_types import (
    DETERMINISTIC_FACTORY_ADDRESS,
    EOA,
    AuthorizationTuple,
    ChainConfig,
    TestPhase,
    Transaction,
    TransactionTestMetadata,
    compute_deterministic_create2_address,
)
from execution_testing.test_types import Alloc as BaseAlloc
from execution_testing.tools import Initcode
from execution_testing.vm import Bytecode, Op

from ..shared.address_stubs import AddressStubs
from ..shared.execute_fill import stub_eoas_key
from ..shared.pre_alloc import Alloc as SharedAlloc
from ..shared.pre_alloc import AllocFlags
from .contracts import (
    check_deterministic_factory_deployment,
    deploy_deterministic_factory_contract,
)

logger = get_logger(__name__)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    pre_alloc_group = parser.getgroup(
        "pre_alloc",
        "Arguments defining pre-allocation behavior during test execution",
    )
    pre_alloc_group.addoption(
        "--eoa-start",
        action="store",
        dest="eoa_iterator_start",
        default=randint(0, 2**256),
        type=int,
        help="The start private key from which tests will deploy EOAs.",
    )
    pre_alloc_group.addoption(
        "--skip-cleanup",
        action="store_true",
        dest="skip_cleanup",
        default=False,
        help="Skip cleanup phase after each test.",
    )


@pytest.hookimpl(trylast=True)
def pytest_report_header(config: pytest.Config) -> list[str]:
    """Pytest hook called to obtain the report header."""
    bold = "\033[1m"
    reset = "\033[39;49m"
    eoa_start = config.getoption("eoa_iterator_start")
    header = [
        (bold + f"Start seed for EOA: {hex(eoa_start)} " + reset),
    ]
    return header


@pytest.fixture(scope="session")
def address_stubs(
    request: pytest.FixtureRequest,
) -> AddressStubs | None:
    """
    Return an address stubs object.

    If the address stubs are not supported by the subcommand, return None.
    """
    address_stubs = request.config.getoption("address_stubs", None)
    if address_stubs is not None:
        logger.info(
            f"Using address stubs with {len(address_stubs.root)} entries"
        )
    else:
        logger.debug("No address stubs configured")
    return address_stubs


@pytest.fixture(scope="session")
def stub_eoas(
    request: pytest.FixtureRequest,
) -> Dict[str, EOA]:
    """Return stub EOAs pre-populated during configuration."""
    return request.config.stash.get(stub_eoas_key, {})


@pytest.fixture(scope="session")
def skip_cleanup(request: pytest.FixtureRequest) -> bool:
    """Return whether to skip cleanup phase after each test."""
    skip = request.config.getoption("skip_cleanup")
    if skip:
        logger.info("Cleanup phase will be skipped after each test")
    else:
        logger.debug("Cleanup phase enabled after each test")
    return skip


@pytest.fixture(scope="session")
def eoa_iterator(request: pytest.FixtureRequest) -> Iterator[EOA]:
    """Return an iterator that generates EOAs."""
    eoa_start = request.config.getoption("eoa_iterator_start")
    print(f"Starting EOA index: {hex(eoa_start)}")
    logger.info(
        f"Initializing EOA iterator with start index: {hex(eoa_start)}"
    )
    return iter(EOA(key=i, nonce=0) for i in count(start=eoa_start))


@pytest.fixture(scope="session", autouse=True)
def execute_required_contracts(
    session_fork: Fork | TransitionFork,
    session_worker_key: EOA,
    eth_rpc: EthRPC,
    sender_funding_transactions_gas_price: int,
    session_temp_folder: Path,
) -> None:
    """
    Deploy required contracts for the execute command.

    - Deterministic deployment proxy

    Proxy deploy failure doesn't abort the session.
    Tests skip deterministic deploys on use.
    Details check `(see Alloc._resolve_deterministic_deploys)`.
    """
    base_lock_file = session_temp_folder / "execute_required_contracts.lock"
    with FileLock(base_lock_file):
        logger.info(
            "Checking if deterministic factory contract is already deployed"
        )
        if (
            check_deterministic_factory_deployment(
                eth_rpc=eth_rpc, fork=session_fork
            )
            is None
        ):
            try:
                deploy_deterministic_factory_contract(
                    eth_rpc=eth_rpc,
                    seed_key=session_worker_key,
                    gas_price=sender_funding_transactions_gas_price,
                )
            except Exception as e:
                logger.warning(
                    "Could not deploy the deterministic deployment proxy; "
                    "tests that require it will be skipped. To deploy it "
                    "manually against a different RPC endpoint run "
                    "`uv run execute deploy-required-contracts`. "
                    f"Reason: {e}"
                )


class PendingTransaction(Transaction):
    """
    Custom transaction class that defines a transaction yet to be sent.

    The value is allowed to be `None` to allow for the value to be set until
    the transaction is sent.
    """

    value: HexNumber | None = None  # type: ignore


@dataclass
class _DeferredDeterministicDeploy:
    """Descriptor for a deferred deterministic contract deployment."""

    contract_address: Address
    deploy_code: Bytes
    salt: Hash
    initcode: Bytes | Initcode
    label: str | None
    deploy_gas_limit: int


@dataclass
class _DeferredStubCheck:
    """Descriptor for a deferred stub contract account fetch."""

    contract_address: Address
    stub: str
    label: str | None


@dataclass
class _DeferredFundAddress:
    """Descriptor for a deferred address funding balance check."""

    address: Address
    amount: int
    minimum_balance: bool


@dataclass
class _DeferredAccountAssertion:
    """
    Deferred assertion on a predeployed account.

    Verified at start_block before the benchmark runs.
    Uses primitives only to stay independent of test expectations.
    """

    address: Address
    is_existing_account: bool
    is_contract: bool
    min_balance: int | None
    code_prefix: bytes | None
    label: str | None


class DeployedAccountVerificationError(AssertionError):
    """Raised when predeployed benchmark targets fail verification."""


def _check_account_assertion(
    d: _DeferredAccountAssertion,
    account: Account | None,
    code: Bytes | None,
) -> list[str]:
    """Return human-readable failures for one account assertion (may be []."""
    who = f"{d.label or '<target>'} at {d.address}"
    if account is None:
        return [f"{who}: no account data returned from the client"]
    balance = int(account.balance)
    nonce = int(account.nonce)
    errors: list[str] = []
    if not d.is_existing_account:
        if balance != 0 or nonce != 0:
            errors.append(
                f"{who}: expected NON-existent, got balance={balance} "
                f"nonce={nonce}"
            )
        return errors
    if d.is_contract and nonce < 1:
        errors.append(
            f"{who}: expected a deployed contract (nonce>=1) but got "
            f"nonce={nonce}, balance={balance} — likely NOT deployed on the "
            "snapshot; the benchmark would silently hit an empty account"
        )
    if d.min_balance is not None and balance < d.min_balance:
        errors.append(
            f"{who}: expected balance>={d.min_balance} but got {balance}"
        )
    if d.code_prefix is not None:
        actual = bytes(code) if code is not None else b""
        if not actual.startswith(d.code_prefix):
            errors.append(
                f"{who}: expected code to start with "
                f"0x{d.code_prefix.hex()} (e.g. a delegated account) but "
                f"got 0x{actual.hex()}"
            )
    return errors


def _compute_deploy_gas_limit(
    fork: Fork,
    *,
    deploy_code_size: int,
    initcode: Bytes | Initcode,
    storage_slots: int = 0,
) -> Tuple[int, int]:
    """
    Compute the deploy transaction gas limit, returning both the execution
    gas portion bound by the EIP 7825 cap and the total execution plus
    state gas used as the transaction gas field. Under EIP 8037 the cap
    binds only the execution portion while state gas comes from the block
    reservoir and may push the total above the cap, and before Amsterdam
    the state gas is zero so the total equals the execution gas. The execution
    portion is doubled as a safety buffer since gas estimation is
    approximate while the state portion is exact.
    """
    gas_costs = fork.gas_costs()
    memory_expansion_gas_calculator = fork.memory_expansion_gas_calculator()
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()

    sstore = Op.SSTORE(new_value=1)
    sstore_state_gas = sstore.state_cost(fork)
    sstore_execution_gas = sstore.gas_cost(fork) - sstore_state_gas

    # The intrinsic cost is now execution-only: the created account's
    # NEW_ACCOUNT state gas is charged at the top frame, not folded in.
    intrinsic_execution_gas = intrinsic_gas_calculator(
        calldata=initcode, contract_creation=True
    )

    # Execution portion, bound by the gas cap.
    execution_gas = intrinsic_execution_gas
    if fork.state_gas_reservoir_enabled():
        execution_gas += gas_costs.OPCODE_KECCAK256_PER_WORD * (
            (deploy_code_size + 31) // 32
        )
    else:
        execution_gas += deploy_code_size * gas_costs.CODE_DEPOSIT_PER_BYTE
    execution_gas += memory_expansion_gas_calculator(
        new_bytes=len(bytes(initcode))
    )
    execution_gas += storage_slots * sstore_execution_gas

    # Double as a safety buffer since gas estimation is approximate. The buffer
    # must not, by itself, push a contract that genuinely deploys within the
    # EIP-7825 execution-gas cap over it: when the unbuffered estimate
    # still fits
    # the cap, clamp the limit to the cap instead. The deploy then runs with a
    # cap-sized execution limit and consumes only its (smaller) actual gas.
    # Only a contract whose unbuffered estimate exceeds the cap is truly
    # undeployable (the caller raises on that).
    buffered_execution_gas = execution_gas * 2
    tx_gas_limit_cap = fork.transaction_gas_limit_cap()
    if (
        tx_gas_limit_cap is not None
        and buffered_execution_gas > tx_gas_limit_cap
        and execution_gas <= tx_gas_limit_cap
    ):
        execution_gas = tx_gas_limit_cap
    else:
        execution_gas = buffered_execution_gas

    # State portion, from the block reservoir. The created account's
    # NEW_ACCOUNT is charged at the top frame for create transactions
    # and by CREATE2 at access for proxy deploys — same amount.
    state_gas = fork.code_deposit_state_gas(code_size=deploy_code_size)
    state_gas += fork.transaction_top_frame_state_gas(contract_creation=True)
    state_gas += storage_slots * sstore_state_gas

    deploy_gas_limit = execution_gas + state_gas
    return execution_gas, deploy_gas_limit


class Alloc(SharedAlloc):
    """A custom class that inherits from the original Alloc class."""

    _sender: EOA = PrivateAttr()
    _eth_rpc: EthRPC = PrivateAttr()
    _pending_txs: List[PendingTransaction] = PrivateAttr(default_factory=list)
    _deployed_contracts: List[Tuple[Address, Bytes | Bytecode]] = PrivateAttr(
        default_factory=list
    )
    _funded_eoa: List[EOA] = PrivateAttr(default_factory=list)
    _chain_id: int = PrivateAttr()
    _node_id: str = PrivateAttr("")
    _address_stubs: AddressStubs = PrivateAttr()
    _deferred_deterministic_deploys: List[_DeferredDeterministicDeploy] = (
        PrivateAttr(default_factory=list)
    )
    _deferred_stub_checks: List[_DeferredStubCheck] = PrivateAttr(
        default_factory=list
    )
    _deferred_fund_addresses: List[_DeferredFundAddress] = PrivateAttr(
        default_factory=list
    )
    _deferred_account_assertions: List[_DeferredAccountAssertion] = (
        PrivateAttr(default_factory=list)
    )
    _block_number: int = PrivateAttr()
    _timestamp: int = PrivateAttr()
    _verify_full: bool = PrivateAttr(default=False)

    def __init__(
        self,
        *args: Any,
        sender: EOA,
        eth_rpc: EthRPC,
        eoa_iterator: Iterator[EOA],
        chain_id: int,
        node_id: str = "",
        address_stubs: AddressStubs | None = None,
        block_number: int = 0,
        timestamp: int = 0,
        funding_gas_limit: int = 200_000,
        verify_full: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize the pre-alloc with the given parameters."""
        super().__init__(*args, **kwargs)
        self._sender = sender
        self._eth_rpc = eth_rpc
        self._eoa_iterator = eoa_iterator
        self._chain_id = chain_id
        self._node_id = node_id
        self._address_stubs = address_stubs or AddressStubs(root={})
        self._block_number = block_number
        self._timestamp = timestamp
        self._funding_gas_limit = funding_gas_limit
        self._verify_full = verify_full

    def code_pre_processor(self, code: Bytecode) -> Bytecode:
        """Pre-processes the code before setting it."""
        return code

    def _add_pending_tx(
        self,
        *,
        action: str | None,
        target: str | None,
        **kwargs: Any,
    ) -> PendingTransaction:
        """
        Prepares a transaction to be sent to the network with the appropriate
        metadata and adds it to the queue.
        """
        if "sender" not in kwargs and "v" not in kwargs:
            kwargs["sender"] = self._sender
        pending_tx = PendingTransaction(
            **kwargs,
        )
        # Pending txs are setup by definition; override Transaction's
        # test_phase default (sourced from TestPhaseManager) so a
        # ``pre.fund_eoa`` call inside ``TestPhaseManager.execution()``
        # doesn't bleed an EXECUTION phase onto a setup tx.
        pending_tx.test_phase = TestPhase.SETUP
        pending_tx.metadata = TransactionTestMetadata(
            test_id=self._node_id,
            phase="setup",
            action=action,
            target=target,
            tx_index=len(self._pending_txs),
        )
        self._pending_txs.append(pending_tx)
        return pending_tx

    def _deterministic_deploy_contract(
        self,
        *,
        deploy_code: BytesConvertible,
        salt: Hash | int,
        initcode: BytesConvertible | None,
        storage: Storage | StorageRootType | None,
        label: str | None,
    ) -> Address:
        """
        Execute implementation of contract deployment to a deterministic
        location.

        Chain verification is deferred to ``resolve_deferred_checks`` so
        that multiple deployments can be batched into a single RPC round
        trip.
        """
        del storage
        fork = self._fork.fork_at(
            block_number=self._block_number, timestamp=self._timestamp
        )
        if not isinstance(deploy_code, Bytes):
            deploy_code = Bytes(deploy_code)
        if initcode is None:
            initcode = Initcode(deploy_code=deploy_code)
        elif not isinstance(initcode, Bytes):
            initcode = Bytes(initcode)
        salt = Hash(salt)
        contract_address = compute_deterministic_create2_address(
            salt=salt, initcode=initcode, fork=fork
        )

        # Pre-compute the gas limit for the deploy transaction.
        max_code_size = fork.max_code_size()
        if len(deploy_code) > max_code_size:
            raise ValueError(
                f"code too large: {len(deploy_code)} > {max_code_size}"
            )
        max_initcode_size = fork.max_initcode_size()
        if len(initcode) > max_initcode_size:
            raise ValueError(
                f"initcode too large {len(initcode)} > {max_initcode_size}"
            )
        execution_gas, deploy_gas_limit = _compute_deploy_gas_limit(
            fork,
            deploy_code_size=len(deploy_code),
            initcode=initcode,
        )
        # Per EIP-8037, the per-tx 2^24 cap (EIP-7825) binds only the
        # execution-gas portion; state gas is drawn from the block reservoir.
        tx_gas_limit_cap = fork.transaction_gas_limit_cap()
        if tx_gas_limit_cap and execution_gas > tx_gas_limit_cap:
            raise ValueError(
                f"deterministic deploy execution gas exceeds the transaction "
                f"gas limit cap: {execution_gas} > {tx_gas_limit_cap}"
            )

        # Defer the on-chain check; the deploy tx (if needed) and the
        # alloc update will happen in resolve_deferred_checks.
        self._deferred_deterministic_deploys.append(
            _DeferredDeterministicDeploy(
                contract_address=contract_address,
                deploy_code=deploy_code,
                salt=salt,
                initcode=initcode,
                label=label,
                deploy_gas_limit=deploy_gas_limit,
            )
        )

        # Set a placeholder so the address is visible in the alloc
        # immediately.
        self.__internal_setitem__(
            contract_address,
            Account(code=deploy_code),
        )

        contract_address.label = label
        return contract_address

    def _deploy_contract(
        self,
        code: BytesConvertible,
        *,
        storage: Storage | StorageRootType | None,
        balance: NumberConvertible,
        nonce: NumberConvertible,
        address: Address | None,
        label: str | None,
        stub: str | None,
    ) -> Address:
        """Execute implementation of contract deployment."""
        if storage is None:
            storage = {}
        assert address is None, "address parameter is not supported"
        fork = self._fork.fork_at(
            block_number=self._block_number, timestamp=self._timestamp
        )

        if not isinstance(storage, Storage):
            storage = Storage(storage)  # type: ignore

        if stub is not None:
            if stub not in self._address_stubs:
                raise ValueError(
                    f"Stub '{stub}' not found in address stubs. "
                    "Provide --address-stubs with a mapping file."
                )
            contract_address = self._address_stubs[stub]
            logger.info(
                f"Using address stub '{stub}' at {contract_address} "
                f"(label={label})"
            )
            # Defer the account fetch; the alloc will be updated in
            # resolve_deferred_checks.
            self._deferred_stub_checks.append(
                _DeferredStubCheck(
                    contract_address=contract_address,
                    stub=stub,
                    label=label,
                )
            )
            # Set a placeholder so the address is visible in the alloc
            # immediately.
            self.__internal_setitem__(
                contract_address,
                Account(code=code),
            )
            contract_address.label = label
            return contract_address

        initcode_prefix = Bytecode()

        if len(storage.root) > 0:
            initcode_prefix += sum(
                Op.SSTORE(key, value) for key, value in storage.root.items()
            )

        assert isinstance(code, Bytecode), (
            f"incompatible code type: {type(code)}"
        )
        code = self.code_pre_processor(code)

        max_code_size = fork.max_code_size()
        if len(code) > max_code_size:
            raise ValueError(f"code too large: {len(code)} > {max_code_size}")

        prepared_initcode = Initcode(
            deploy_code=code, initcode_prefix=initcode_prefix
        )

        max_initcode_size = fork.max_initcode_size()
        initcode_len = len(prepared_initcode)
        if initcode_len > max_initcode_size:
            raise ValueError(
                f"initcode too large {initcode_len} > {max_initcode_size}"
            )

        execution_gas, deploy_gas_limit = _compute_deploy_gas_limit(
            fork,
            deploy_code_size=len(code),
            initcode=prepared_initcode,
            storage_slots=len(storage.root),
        )
        # Per EIP-8037, the per-tx 2^24 cap (EIP-7825) binds only the
        # execution-gas portion; state gas is drawn from the block reservoir.
        tx_gas_limit_cap = fork.transaction_gas_limit_cap()
        if tx_gas_limit_cap and execution_gas > tx_gas_limit_cap:
            raise ValueError(
                f"deploy execution gas exceeds the transaction gas limit cap: "
                f"{execution_gas} > {tx_gas_limit_cap}"
            )

        deploy_tx = self._add_pending_tx(
            action="deploy_contract",
            target=label,
            to=None,
            data=prepared_initcode,
            value=balance,
            gas_limit=deploy_gas_limit,
        )
        code_sz = len(code)
        init_sz = len(prepared_initcode)
        bal_eth = Number(balance) / 10**18
        slots = len(storage.root)
        logger.info(
            f"Contract deployment tx created (label={label}): "
            f"tx_nonce={deploy_tx.nonce}, gas_limit={deploy_gas_limit}, "
            f"code_size={code_sz} bytes, initcode_size={init_sz} bytes, "
            f"balance={bal_eth:.18f} ETH, storage_slots={slots}"
        )

        contract_address = deploy_tx.created_contract
        logger.debug(
            f"Contract will be deployed at {contract_address} "
            f"(label={label}, tx_index={len(self._pending_txs) - 1})"
        )
        self._deployed_contracts.append((contract_address, code))

        assert Number(nonce) >= 1, (
            "impossible to deploy contract with nonce lower than one"
        )

        self.__internal_setitem__(
            contract_address,
            Account(
                nonce=nonce,
                balance=balance,
                code=code,
                storage=storage,
            ),
        )

        contract_address.label = label
        return contract_address

    def _fund_eoa(
        self,
        amount: NumberConvertible | None,
        label: str | None,
        storage: Storage | StorageRootType | None,
        code: BytesConvertible | None,
        delegation: Address | Literal["Self"] | None,
        nonce: NumberConvertible | None,
    ) -> EOA:
        """
        Execute implementation of EOA funding.
        """
        assert nonce is None, "nonce parameter is not supported for execute"
        assert code is None, "code parameter is not supported for execute"
        eoa = next(self._eoa_iterator)
        eoa.label = label
        amount_str = (
            f"{Number(amount) / 10**18:.18f} ETH"
            if amount is not None
            else "Deferred"
        )
        logger.debug(
            f"Funding EOA {eoa} (label={label}): amount={amount_str}, "
            f"delegation={delegation}, storage={storage is not None}"
        )
        # Send a transaction to fund the EOA
        fund_tx: PendingTransaction | None = None
        if delegation is not None or storage is not None:
            fork = self._fork.fork_at(
                block_number=self._block_number, timestamp=self._timestamp
            )
            intrinsic_calc = fork.transaction_intrinsic_cost_calculator()

            worst_case_auth = [
                AuthorizationTuple(
                    address=Address(0),
                    v=0,
                    r=0,
                    s=0,
                    creates_account=True,
                    writes_delegation=True,
                    first_write=True,
                )
            ]
            auth_fund_gas_limit = intrinsic_calc(
                authorization_list_or_count=1,
                sends_value=True,
                recipient_type=RecipientType.EMPTY_ACCOUNT,
            ) + fork.transaction_top_frame_gas_calculator()(
                sends_value=True,
                recipient_type=RecipientType.EMPTY_ACCOUNT,
                authorizations=worst_case_auth,
            )

            if storage is not None:
                if not isinstance(storage, Storage):
                    storage = Storage.model_validate(storage)
                logger.debug(
                    f"Deploying storage contract for EOA {eoa} "
                    f"with {len(storage)} storage slots"
                )

                storage_init_code = (
                    sum(
                        Op.SSTORE(
                            key,
                            value,
                            # gas accounting
                            key_warm=False,
                            original_value=0,
                            current_value=0,
                            new_value=1,
                        )
                        for key, value in storage.items()
                    )
                    + Op.STOP
                )
                sstore_address = self.deploy_contract(
                    code=storage_init_code,
                )
                logger.debug(
                    f"Storage contract deployed at {sstore_address} "
                    f"for EOA {eoa}"
                )

                self._add_pending_tx(
                    action="eoa_storage_set",
                    target=label,
                    to=eoa,
                    value=0,
                    authorization_list=[
                        AuthorizationTuple(
                            chain_id=self._chain_id,
                            address=sstore_address,
                            nonce=eoa.nonce,
                            signer=eoa,
                        ),
                    ],
                    gas_limit=(
                        intrinsic_calc(authorization_list_or_count=1)
                        + storage_init_code.gas_cost(fork)
                        + 500_000
                    ),
                )
                eoa.nonce = Number(eoa.nonce + 1)

            if delegation is not None:
                if (
                    not isinstance(delegation, Address)
                    and delegation == "Self"
                ):
                    delegation = eoa
                # TODO: This tx has side-effects on the EOA state because of
                # the delegation
                fund_tx = self._add_pending_tx(
                    action="fund_eoa",
                    target=label,
                    to=eoa,
                    value=amount,
                    authorization_list=[
                        AuthorizationTuple(
                            chain_id=self._chain_id,
                            address=delegation,
                            nonce=eoa.nonce,
                            signer=eoa,
                        ),
                    ],
                    gas_limit=auth_fund_gas_limit,
                )
                eoa.nonce = Number(eoa.nonce + 1)
            else:
                fund_tx = self._add_pending_tx(
                    action="fund_eoa",
                    target=label,
                    to=eoa,
                    value=amount if amount is not None else 0,
                    authorization_list=[
                        AuthorizationTuple(
                            chain_id=self._chain_id,
                            # Reset delegation to an address without code
                            address=0,
                            nonce=eoa.nonce,
                            signer=eoa,
                        ),
                    ],
                    gas_limit=auth_fund_gas_limit,
                )
                eoa.nonce = Number(eoa.nonce + 1)

        else:
            if amount is None or Number(amount) > 0:
                fund_tx = self._add_pending_tx(
                    action="fund_eoa",
                    target=label,
                    to=eoa,
                    value=amount,
                    gas_limit=self._funding_gas_limit,
                )

        if fund_tx is not None:
            logger.info(
                f"Added funding transaction for EOA {eoa} (label={label}): "
                f"tx_nonce={fund_tx.nonce}, "
                f"tx_index={len(self._pending_txs) - 1}"
            )
        account_kwargs: Dict[str, Any] = {
            "nonce": eoa.nonce,
        }
        if amount is not None:
            account_kwargs["balance"] = amount
        account = Account(**account_kwargs)
        self.__internal_setitem__(eoa, account)
        self._funded_eoa.append(eoa)
        balance_str = (
            f"{Number(amount) / 10**18:.18f} ETH"
            if amount is not None
            else "Deferred"
        )
        logger.info(
            f"EOA {eoa} funding tx created (label={label}):"
            f"tx_nonce={eoa.nonce}, balance={balance_str}"
        )
        return eoa

    def _fund_address(
        self,
        address: Address,
        amount: int,
        *,
        minimum_balance: bool,
    ) -> None:
        """
        Execute implementation of address funding.

        The balance check is deferred to ``resolve_deferred_checks`` so
        that multiple fund_address calls can be batched into a single
        RPC round trip.
        """
        self._deferred_fund_addresses.append(
            _DeferredFundAddress(
                address=address,
                amount=amount,
                minimum_balance=minimum_balance,
            )
        )
        self.__internal_setitem__(address, Account(balance=amount))

    def _nonexistent_account(self) -> Address:
        """
        Execute implementation of nonexistent_account.

        Return a previously unused address. The account is not
        created on-chain — it remains nonexistent.
        """
        eoa = next(self._eoa_iterator)
        logger.debug(f"Returning unused address {eoa} (nonexistent account)")
        return Address(eoa)

    def expect_account_state(
        self,
        addresses: Address | Sequence[Address],
        *,
        is_existing_account: bool = True,
        is_contract: bool = False,
        min_balance: int | None = None,
        code_prefix: bytes | None = None,
    ) -> None:
        """
        Register deferred assertion(s) on predeployed account(s).

        Verified at start_block (fill-stateful only). For a range, only the
        first and last are checked unless ``--verify-full-accounts`` is set;
        each assertion's label is taken from the address itself.
        """
        if isinstance(addresses, Address):
            targets: Sequence[Address] = (addresses,)
        elif self._verify_full or len(addresses) <= 2:
            targets = addresses
        else:
            targets = (addresses[0], addresses[-1])
        for address in targets:
            self._deferred_account_assertions.append(
                _DeferredAccountAssertion(
                    address=address,
                    is_existing_account=is_existing_account,
                    is_contract=is_contract,
                    min_balance=min_balance,
                    code_prefix=code_prefix,
                    label=address.label,
                )
            )

    def verify_deployed_accounts(self, block_number: int) -> None:
        """
        Verify registered predeployed-account assertions at block_number.

        Batches eth_getBalance and eth_getTransactionCount queries.
        Fetches code only for assertions with code_prefix (e.g., EIP-7702
        designation). Collects all failures before raising.
        """
        deferred = self._deferred_account_assertions
        self._deferred_account_assertions = []
        if not deferred:
            return

        chunk, max_reported, verified = 2000, 20, 0
        for i in range(0, len(deferred), chunk):
            batch = deferred[i : i + chunk]

            query = BaseAlloc(root={d.address: Account() for d in batch})
            accounts = self._eth_rpc.get_alloc(
                query, block_number=block_number, skip_code=True
            ).root

            code_targets = [
                d.address for d in batch if d.code_prefix is not None
            ]
            codes: dict[Address, Bytes] = dict(
                zip(
                    code_targets,
                    self._eth_rpc.get_codes(
                        code_targets, block_number=block_number
                    ),
                    strict=True,
                )
            )

            errors: list[str] = []
            failed = 0
            for d in batch:
                errs = _check_account_assertion(
                    d, accounts.get(d.address), codes.get(d.address)
                )
                if errs:
                    failed += 1
                    errors.extend(errs)

            if errors:
                shown = errors[:max_reported]
                omitted = len(errors) - len(shown)
                suffix = f"\n  ... and {omitted} more" if omitted else ""
                raise DeployedAccountVerificationError(
                    f"{failed} predeployed benchmark target(s) failed "
                    f"verification at start_block (after checking "
                    f"{verified + len(batch)}):\n  "
                    + "\n  ".join(shown)
                    + suffix
                )
            verified += len(batch)

        logger.info(
            f"Verified {verified} predeployed benchmark target(s) at "
            f"block {block_number}"
        )

    def resolve_deferred_checks(self) -> None:
        """
        Resolve all deferred on-chain checks using batched RPC calls.

        Must be called after the test function finishes and before
        ``minimum_balance_for_pending_transactions``.  This turns the
        deferred descriptors into concrete pending transactions and
        updates the alloc with real on-chain data.
        """
        self._resolve_deterministic_deploys()
        self._resolve_stub_checks()
        self._resolve_fund_addresses()

    def _resolve_deterministic_deploys(self) -> None:
        """Batch-resolve deferred deterministic contract deployments."""
        deferred = self._deferred_deterministic_deploys
        if not deferred:
            return
        fork = self._fork.fork_at(
            block_number=self._block_number, timestamp=self._timestamp
        )
        self._deferred_deterministic_deploys = []

        addresses = [d.contract_address for d in deferred]
        chain_codes = self._eth_rpc.get_codes(addresses)

        factory_checked = False

        for d, chain_code in zip(deferred, chain_codes, strict=True):
            if chain_code != b"":
                assert chain_code == d.deploy_code, (
                    "Deterministic deployed contract's code on chain "
                    "does not match the expected code: "
                    f"Expected: {d.deploy_code}, "
                    f"Current: {chain_code}"
                )
                logger.info(
                    f"Contract already deployed at {d.contract_address} "
                    f"(label={d.label})"
                )
            else:
                if not factory_checked:
                    if (
                        check_deterministic_factory_deployment(
                            eth_rpc=self._eth_rpc, fork=fork
                        )
                        is None
                    ):
                        pytest.skip(
                            "deterministic deployment proxy is not available "
                            "on this network; skipping test that requires a "
                            "deterministic contract deployment"
                        )
                    factory_checked = True

                logger.info(
                    f"Contract {d.contract_address} not found, "
                    f"deploying (label={d.label})"
                )
                deploy_tx = self._add_pending_tx(
                    action="deterministic_deploy_contract",
                    target=d.label,
                    to=DETERMINISTIC_FACTORY_ADDRESS,
                    data=Bytes(d.salt) + Bytes(d.initcode),
                    gas_limit=d.deploy_gas_limit,
                    value=0,
                )
                code_size = len(d.deploy_code)
                initcode_size = len(d.initcode)
                logger.info(
                    f"Contract deployment tx created (label={d.label}): "
                    f"tx_nonce={deploy_tx.nonce}, "
                    f"gas_limit={d.deploy_gas_limit}, "
                    f"code_size={code_size} bytes, "
                    f"initcode_size={initcode_size} bytes"
                )
                logger.debug(
                    f"Contract will be deployed at "
                    f"{d.contract_address} "
                    f"(label={d.label}, "
                    f"tx_index={len(self._pending_txs) - 1})"
                )
                self._deployed_contracts.append(
                    (d.contract_address, d.deploy_code)
                )

        # Batch-fetch the current account state for all addresses and
        # update the alloc.
        alloc_query = BaseAlloc(root={addr: Account() for addr in addresses})
        actual_alloc = self._eth_rpc.get_alloc(alloc_query)
        for addr in addresses:
            account = actual_alloc.root.get(addr)
            if account is not None:
                self.__internal_setitem__(addr, account)

    def _resolve_stub_checks(self) -> None:
        """Batch-resolve deferred stub contract account fetches."""
        deferred = self._deferred_stub_checks
        if not deferred:
            return
        self._deferred_stub_checks = []

        alloc_query = BaseAlloc(
            root={d.contract_address: Account() for d in deferred}
        )
        actual_alloc = self._eth_rpc.get_alloc(alloc_query)

        for d in deferred:
            account = actual_alloc.root.get(d.contract_address)
            assert account is not None, (
                f"Failed to fetch account for stub '{d.stub}' "
                f"at {d.contract_address}"
            )
            if account.code == b"":
                raise ValueError(
                    f"Stub {d.stub} at {d.contract_address} has no code"
                )
            bal_eth = account.balance / 10**18
            logger.debug(
                f"Stub contract {d.contract_address}: "
                f"balance={bal_eth:.18f} ETH, "
                f"nonce={account.nonce}, "
                f"code_size={len(account.code)} bytes"
            )
            self.__internal_setitem__(d.contract_address, account)

    def _resolve_fund_addresses(self) -> None:
        """Batch-resolve deferred address funding balance checks."""
        deferred = self._deferred_fund_addresses
        if not deferred:
            return
        self._deferred_fund_addresses = []

        addresses = [d.address for d in deferred]
        current_balances = self._eth_rpc.get_balances(addresses)

        for d, current_balance in zip(deferred, current_balances, strict=True):
            if d.minimum_balance:
                if current_balance >= d.amount:
                    cur_eth = current_balance / 10**18
                    min_eth = d.amount / 10**18
                    logger.info(
                        f"Skipping funding for address {d.address} "
                        f"(label={d.address.label}): current balance "
                        f"{cur_eth:.18f} ETH >= minimum "
                        f"{min_eth:.18f} ETH"
                    )
                    self.__internal_setitem__(
                        d.address, Account(balance=current_balance)
                    )
                    continue
                fund_eth = d.amount / 10**18
                logger.debug(
                    f"Funding address to minimum balance {d.address} "
                    f"(label={d.address.label}): {fund_eth:.18f} ETH"
                )
                self._add_pending_tx(
                    action="fund_address",
                    target=d.address.label,
                    to=d.address,
                    value=d.amount - current_balance,
                    gas_limit=self._funding_gas_limit,
                )
                new_balance = d.amount
            else:
                fund_eth = d.amount / 10**18
                logger.debug(
                    f"Funding address {d.address} "
                    f"(label={d.address.label}): "
                    f"{fund_eth:.18f} ETH"
                )
                self._add_pending_tx(
                    action="fund_address",
                    target=d.address.label,
                    to=d.address,
                    value=d.amount,
                    gas_limit=self._funding_gas_limit,
                )
                new_balance = current_balance + d.amount

            self.__internal_setitem__(d.address, Account(balance=new_balance))
            logger.info(
                f"Address {d.address} funding tx created "
                f"(label={d.address.label}): "
                f"{Number(d.amount) / 10**18:.18f} ETH"
            )

    def minimum_balance_for_pending_transactions(
        self,
        sender_balances: Dict[Address, int],
        gas_price: int,
        max_fee_per_gas: int,
        max_priority_fee_per_gas: int,
        max_fee_per_blob_gas: int,
    ) -> Tuple[int, int]:
        """
        Calculate the minimum balance required by the sender to send all
        pending transactions.
        """
        minimum_balance = 0
        gas_consumption = 0
        fork = self._fork.fork_at(
            block_number=self._block_number, timestamp=self._timestamp
        )
        for tx in self._pending_txs:
            if tx.value is None:
                # WARN: This currently fails if there's an account with
                # `pre.fund_eoa()` that never sends a transaction during test.
                if tx.to not in sender_balances:
                    error_message = (
                        "Sender balance must be set before sending:"
                        f"\nTransaction: {tx.model_dump_json(indent=2)}"
                    )
                    if tx.metadata is not None:
                        metadata_json = tx.metadata.model_dump_json(indent=2)
                        error_message += f"\nMetadata: {metadata_json}"
                    logger.error(error_message)
                    raise ValueError(error_message)
                sender_balance = sender_balances[tx.to]
                bal_eth = sender_balance / 10**18
                logger.info(
                    f"Deferred EOA balance for {tx.to} set to "
                    f"{bal_eth:.18f} ETH"
                )
                tx.value = HexNumber(sender_balance)
            tx.set_gas_price(
                gas_price=gas_price,
                max_fee_per_gas=max_fee_per_gas,
                max_priority_fee_per_gas=max_priority_fee_per_gas,
                max_fee_per_blob_gas=max_fee_per_blob_gas,
            )
            assert "gas_limit" in tx.model_fields_set, "tx gas limit not set"
            gas_consumption += tx.gas_limit
            minimum_balance += tx.signer_minimum_balance(fork=fork)
        return minimum_balance + gas_consumption * gas_price, gas_consumption

    def send_pending_transactions(self) -> List[TransactionByHashResponse]:
        """Send all pending transactions and wait for them to be included."""
        logger.info(
            f"Sending {len(self._pending_txs)} pending transactions "
            f"(deployed_contracts={len(self._deployed_contracts)}, "
            f"funded_eoas={len(self._funded_eoa)})"
        )
        for tx in self._pending_txs:
            assert tx.value is not None, (
                "Transaction value must be set before sending them to the RPC."
            )

        txs = [tx.with_signature_and_sender() for tx in self._pending_txs]
        responses = self._eth_rpc.send_wait_transactions(txs)

        for response in responses:
            logger.debug(f"Transaction response: {response.model_dump_json()}")
        return responses

    def pending_transactions(self) -> List[Transaction]:
        """
        Return the queued setup transactions, signed; clears the queue.

        Used by fill-stateful to materialise ``pre.fund_eoa`` /
        ``pre.deploy_contract`` calls into a synthetic setup block.
        Unset ``value`` is coerced to ``0`` (live-send path would default
        it before broadcast).
        """
        txs: List[Transaction] = []
        for tx in self._pending_txs:
            if tx.value is None:
                tx.value = HexNumber(0)
            txs.append(tx.with_signature_and_sender())
        self._pending_txs.clear()
        return txs


@pytest.fixture(scope="function")
def alloc_flags(
    alloc_flags_from_test_markers: AllocFlags,
) -> AllocFlags:
    """
    Verify this test does not require flags that are unsupported by execute.

    Otherwise skip.
    """
    if AllocFlags.MUTABLE in alloc_flags_from_test_markers:
        pytest.skip(
            "Execute mode cannot run tests where the pre-alloction is mutated."
        )

    return alloc_flags_from_test_markers


@pytest.fixture(autouse=True, scope="function")
def pre(
    fork: Fork,
    alloc_flags: AllocFlags,
    worker_key: EOA,
    eoa_iterator: Iterator[EOA],
    eth_rpc: EthRPC,
    chain_config: ChainConfig,
    address_stubs: AddressStubs | None,
    stub_eoas: Dict[str, EOA],
    skip_cleanup: bool,
    max_fee_per_gas: int,
    max_priority_fee_per_gas: int,
    dry_run: bool,
    sender_fund_refund_gas_limit: int,
    request: pytest.FixtureRequest,
) -> Generator[Alloc, None, None]:
    """Return default pre allocation for all tests (Empty alloc)."""
    # Prepare the pre-alloc
    logger.debug(
        f"Initializing pre-alloc for test {request.node.nodeid} "
        f"(fork={fork}, chain_id={chain_config.chain_id})"
    )
    pre = Alloc(
        fork=fork,
        flags=alloc_flags,
        stub_eoas=stub_eoas,
        sender=worker_key,
        eth_rpc=eth_rpc,
        eoa_iterator=eoa_iterator,
        chain_id=chain_config.chain_id,
        node_id=request.node.nodeid,
        address_stubs=address_stubs,
        funding_gas_limit=sender_fund_refund_gas_limit,
        verify_full=getattr(
            request.config.option, "verify_full_accounts", False
        ),
    )

    # Yield the pre-alloc for usage during the test
    yield pre

    if dry_run:
        logger.debug("Dry run: skipping cleanup phase")
        return
    if skip_cleanup:
        logger.info("Skipping cleanup phase as requested")
        return

    # Refund all EOAs (regardless of whether the test passed or failed)
    funded_eoas = pre._funded_eoa
    logger.info(
        f"Starting cleanup phase: refunding {len(funded_eoas)} funded EOAs"
    )

    if not funded_eoas:
        logger.info("No funded EOAs to refund")
        return

    # Build refund transactions
    refund_txs: List[Transaction] = []
    skipped_refunds = 0
    refund_gas_limit = sender_fund_refund_gas_limit
    tx_cost = refund_gas_limit * max_fee_per_gas
    for idx, eoa in enumerate(funded_eoas):
        account = eth_rpc.get_account(eoa, skip_code=True)
        remaining_balance = account.balance
        eoa.nonce = Number(account.nonce)
        if remaining_balance < tx_cost:
            rem_eth = remaining_balance / 10**18
            cost_eth = tx_cost / 10**18
            logger.debug(
                f"Skipping refund for EOA {eoa} "
                f"(label={eoa.label}): "
                f"insufficient balance {rem_eth:.18f} ETH < "
                f"transaction cost {cost_eth:.18f} ETH"
            )
            skipped_refunds += 1
            continue
        refund_value = remaining_balance - tx_cost
        ref_eth = refund_value / 10**18
        rem_eth = remaining_balance / 10**18
        cost_eth = tx_cost / 10**18
        logger.debug(
            f"Preparing refund transaction for EOA {eoa} "
            f"(label={eoa.label}): "
            f"{ref_eth:.18f} ETH (remaining: {rem_eth:.18f} ETH, "
            f"cost: {cost_eth:.18f} ETH)"
        )
        refund_tx = Transaction(
            sender=eoa,
            to=worker_key,
            gas_limit=refund_gas_limit,
            max_fee_per_gas=max_fee_per_gas,
            max_priority_fee_per_gas=max_priority_fee_per_gas,
            value=refund_value,
        ).with_signature_and_sender()
        refund_tx.metadata = TransactionTestMetadata(
            test_id=request.node.nodeid,
            phase="cleanup",
            action="refund_from_eoa",
            target=eoa.label,
            tx_index=idx,
        )
        refund_txs.append(refund_tx)

    if refund_txs:
        logger.info(
            f"Sending {len(refund_txs)} refund transactions "
            f"({skipped_refunds} skipped due to insufficient balance)"
        )
        eth_rpc.send_wait_transactions(refund_txs)
        logger.info(f"All {len(refund_txs)} refund transactions confirmed")
    else:
        logger.info(
            f"No refund transactions to send "
            f"({skipped_refunds} EOAs skipped "
            f"due to insufficient balance)"
        )
