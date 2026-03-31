"""Pre-allocation fixtures used for test filling."""

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
from execution_testing.base_types import (
    Alloc as BaseAlloc,
)
from execution_testing.base_types.conversions import (
    BytesConvertible,
    NumberConvertible,
)
from execution_testing.forks import Fork, TransitionFork
from execution_testing.logging import get_logger
from execution_testing.rpc import EthRPC
from execution_testing.rpc.rpc_types import TransactionByHashResponse
from execution_testing.test_types import (
    DETERMINISTIC_FACTORY_ADDRESS,
    EOA,
    AuthorizationTuple,
    ChainConfig,
    Transaction,
    TransactionTestMetadata,
    compute_deterministic_create2_address,
)
from execution_testing.tools import Initcode
from execution_testing.vm import Bytecode, Op

from ..shared.address_stubs import AddressStubs
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
    """
    base_lock_file = session_temp_folder / "execute_required_contracts.lock"
    with FileLock(base_lock_file):
        logger.info(
            "Checking if deterministic factory contract is already deployed"
        )
        tx_index = 0
        if (
            check_deterministic_factory_deployment(
                eth_rpc=eth_rpc, fork=session_fork
            )
            is None
        ):
            try:
                tx_index = deploy_deterministic_factory_contract(
                    eth_rpc=eth_rpc,
                    seed_key=session_worker_key,
                    gas_price=sender_funding_transactions_gas_price,
                    tx_index=tx_index,
                )
            except Exception as e:
                raise RuntimeError(
                    f"Error deploying deterministic deployment contract:\n{e}"
                    "\nTry deploying the contract manually using a different "
                    "RPC endpoint with the following command:\n"
                    "uv run execute deploy-required-contracts"
                ) from e


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
    _block_number: int = PrivateAttr()
    _timestamp: int = PrivateAttr()

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
        gas_costs = fork.gas_costs()
        memory_expansion_gas_calculator = (
            fork.memory_expansion_gas_calculator()
        )
        calldata_gas_calculator = fork.calldata_gas_calculator()
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
        deploy_gas_limit = gas_costs.GAS_TX_BASE + gas_costs.GAS_TX_CREATE
        deploy_gas_limit += (
            len(deploy_code) * gas_costs.GAS_CODE_DEPOSIT_PER_BYTE
        )
        deploy_gas_limit += memory_expansion_gas_calculator(
            new_bytes=len(initcode)
        )
        deploy_gas_limit += calldata_gas_calculator(data=initcode)
        deploy_gas_limit = deploy_gas_limit * 2
        tx_gas_limit_cap = fork.transaction_gas_limit_cap()
        if tx_gas_limit_cap and deploy_gas_limit > tx_gas_limit_cap:
            raise ValueError(
                f"deterministic deploy gas limit exceeds the transaction "
                f"gas limit cap: {deploy_gas_limit} > {tx_gas_limit_cap}"
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
        gas_costs = fork.gas_costs()
        memory_expansion_gas_calculator = (
            fork.memory_expansion_gas_calculator()
        )
        calldata_gas_calculator = fork.calldata_gas_calculator()

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

        deploy_gas_limit = gas_costs.GAS_TX_BASE + gas_costs.GAS_TX_CREATE

        if len(storage.root) > 0:
            initcode_prefix += sum(
                Op.SSTORE(key, value) for key, value in storage.root.items()
            )
            deploy_gas_limit += len(storage.root) * 22_600

        assert isinstance(code, Bytecode), (
            f"incompatible code type: {type(code)}"
        )
        code = self.code_pre_processor(code)

        max_code_size = fork.max_code_size()
        if len(code) > max_code_size:
            raise ValueError(f"code too large: {len(code)} > {max_code_size}")

        deploy_gas_limit += len(code) * gas_costs.GAS_CODE_DEPOSIT_PER_BYTE

        prepared_initcode = Initcode(
            deploy_code=code, initcode_prefix=initcode_prefix
        )
        deploy_gas_limit += memory_expansion_gas_calculator(
            new_bytes=len(bytes(prepared_initcode))
        )

        max_initcode_size = fork.max_initcode_size()
        initcode_len = len(prepared_initcode)
        if initcode_len > max_initcode_size:
            raise ValueError(
                f"initcode too large {initcode_len} > {max_initcode_size}"
            )

        deploy_gas_limit += calldata_gas_calculator(data=prepared_initcode)

        deploy_gas_limit = deploy_gas_limit * 2
        tx_gas_limit_cap = fork.transaction_gas_limit_cap()
        if tx_gas_limit_cap and deploy_gas_limit > tx_gas_limit_cap:
            raise ValueError(
                f"deploy gas limit exceeds the transaction gas limit cap: "
                f"{deploy_gas_limit} > {tx_gas_limit_cap}"
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
            if storage is not None:
                if not isinstance(storage, Storage):
                    storage = Storage.model_validate(storage)
                logger.debug(
                    f"Deploying storage contract for EOA {eoa} "
                    f"with {len(storage)} storage slots"
                )
                sstore_address = self.deploy_contract(
                    code=(
                        sum(
                            Op.SSTORE(key, value)
                            for key, value in storage.items()
                        )
                        + Op.STOP
                    )
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
                    gas_limit=100_000,
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
                    gas_limit=100_000,
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
                    gas_limit=100_000,
                )
                eoa.nonce = Number(eoa.nonce + 1)

        else:
            if amount is None or Number(amount) > 0:
                fund_tx = self._add_pending_tx(
                    action="fund_eoa",
                    target=label,
                    to=eoa,
                    value=amount,
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
                    assert (
                        check_deterministic_factory_deployment(
                            eth_rpc=self._eth_rpc, fork=fork
                        )
                        is not None
                    ), "Deployment contract code is not found"
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
    skip_cleanup: bool,
    max_fee_per_gas: int,
    max_priority_fee_per_gas: int,
    dry_run: bool,
    request: pytest.FixtureRequest,
) -> Generator[Alloc, None, None]:
    """Return default pre allocation for all tests (Empty alloc)."""
    # FIXME: Static tests don't have a fork so we need to get it from the node.
    actual_fork = fork
    if actual_fork is None:
        assert hasattr(request.node, "fork")
        actual_fork = request.node.fork

    # Prepare the pre-alloc
    logger.debug(
        f"Initializing pre-alloc for test {request.node.nodeid} "
        f"(fork={actual_fork}, chain_id={chain_config.chain_id})"
    )
    pre = Alloc(
        fork=actual_fork,
        flags=alloc_flags,
        sender=worker_key,
        eth_rpc=eth_rpc,
        eoa_iterator=eoa_iterator,
        chain_id=chain_config.chain_id,
        node_id=request.node.nodeid,
        address_stubs=address_stubs,
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
    refund_gas_limit = 21_000
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
