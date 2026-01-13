"""Pre-allocation fixtures used for test filling."""

from itertools import count
from pathlib import Path
from random import randint
from typing import Any, Dict, Generator, Iterator, List, Literal, Self, Tuple

import pytest
import yaml
from filelock import FileLock
from pydantic import PrivateAttr

from execution_testing.base_types import (
    Account,
    Address,
    Bytes,
    EthereumTestRootModel,
    Hash,
    HexNumber,
    Number,
    Storage,
    StorageRootType,
    ZeroPaddedHexNumber,
)
from execution_testing.base_types.conversions import (
    BytesConvertible,
    FixedSizeBytesConvertible,
    NumberConvertible,
)
from execution_testing.forks import Fork
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
from execution_testing.test_types import Alloc as BaseAlloc
from execution_testing.tools import Initcode
from execution_testing.vm import Bytecode, Op

from .contracts import (
    check_deterministic_factory_deployment,
    deploy_deterministic_factory_contract,
)

logger = get_logger(__name__)


class AddressStubs(EthereumTestRootModel[Dict[str, Address]]):
    """
    Address stubs class.

    The key represents the label that is used in the test to tag the contract,
    and the value is the address where the contract is already located at in
    the current network.
    """

    root: Dict[str, Address]

    def __contains__(self, item: str) -> bool:
        """Check if an item is in the address stubs."""
        return item in self.root

    def __getitem__(self, item: str) -> Address:
        """Get an item from the address stubs."""
        return self.root[item]

    @classmethod
    def model_validate_json_or_file(cls, json_data_or_path: str) -> Self:
        """
        Try to load from file if the value resembles a path that ends with
        .json/.yml and the file exists.
        """
        lower_json_data_or_path = json_data_or_path.lower()
        if (
            lower_json_data_or_path.endswith(".json")
            or lower_json_data_or_path.endswith(".yml")
            or lower_json_data_or_path.endswith(".yaml")
        ):
            path = Path(json_data_or_path)
            if path.is_file():
                path_suffix = path.suffix.lower()
                if path_suffix == ".json":
                    return cls.model_validate_json(path.read_text())
                elif path_suffix in [".yml", ".yaml"]:
                    loaded_yaml = yaml.safe_load(path.read_text())
                    if loaded_yaml is None:
                        return cls(root={})
                    return cls.model_validate(loaded_yaml)
        if json_data_or_path.strip() == "":
            return cls(root={})
        return cls.model_validate_json(json_data_or_path)


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
    session_fork: Fork,
    session_worker_key: EOA,
    eth_rpc: EthRPC,
    sender_funding_transactions_gas_price: int,
    session_temp_folder: Path,
) -> None:
    """
    Deploy required contracts for the execute command:

    - Deterministic deployment proxy
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
                raise RuntimeError(
                    f"Error deploying deterministic deployment contract:\n{e}"
                    "\nTry deploying the contract manually using a different "
                    "RPC endpoint with the following command:\n"
                    "uv run execute deploy-required-contracts"
                ) from e


class PendingTransaction(Transaction):
    """
    Custom transaction class that defines a transaction that is yet to be sent.
    The value is allowed to be `None` to allow for the value to be set until the
    transaction is sent.
    """

    value: HexNumber | None = None  # type: ignore


class Alloc(BaseAlloc):
    """A custom class that inherits from the original Alloc class."""

    _fork: Fork = PrivateAttr()
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

    def __init__(
        self,
        *args: Any,
        fork: Fork,
        sender: EOA,
        eth_rpc: EthRPC,
        eoa_iterator: Iterator[EOA],
        chain_id: int,
        node_id: str = "",
        address_stubs: AddressStubs | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the pre-alloc with the given parameters."""
        super().__init__(*args, **kwargs)
        self._fork = fork
        self._sender = sender
        self._eth_rpc = eth_rpc
        self._eoa_iterator = eoa_iterator
        self._chain_id = chain_id
        self._node_id = node_id
        self._address_stubs = address_stubs or AddressStubs(root={})

    def __setitem__(
        self,
        address: Address | FixedSizeBytesConvertible,
        account: Account | None,
    ) -> None:
        """Set account associated with an address."""
        raise ValueError(
            "Tests are not allowed to set pre-alloc items in execute mode"
        )

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

    def deterministic_deploy_contract(
        self,
        *,
        deploy_code: BytesConvertible,
        salt: Hash | int = 0,
        initcode: BytesConvertible | None = None,
        storage: Storage | StorageRootType | None = None,
        label: str | None = None,
    ) -> Address:
        """
        Deploy a contract to the allocation at a deterministic location
        using a deterministic deployment proxy.
        """
        gas_costs = self._fork.gas_costs()
        memory_expansion_gas_calculator = (
            self._fork.memory_expansion_gas_calculator()
        )
        calldata_gas_calculator = self._fork.calldata_gas_calculator(
            block_number=0, timestamp=0
        )
        if not isinstance(deploy_code, Bytes):
            deploy_code = Bytes(deploy_code)
        if initcode is None:
            initcode = Initcode(deploy_code=deploy_code)
        elif not isinstance(initcode, Bytes):
            initcode = Bytes(initcode)
        salt = Hash(salt)
        contract_address = compute_deterministic_create2_address(
            salt=salt, initcode=initcode, fork=self._fork
        )
        # 1) Determine if this contract already exists
        chain_code = self._eth_rpc.get_code(contract_address)
        if chain_code != b"":
            assert chain_code == deploy_code, (
                "Deterministic deployed contract's code on chain does not "
                "match the expected code: "
                f"Expected: {deploy_code}, "
                f"Current: {chain_code}"
            )
            logger.info(
                f"Contract already deployed at {contract_address} (label={label})"
            )
        else:
            # Assert the deployment contract is already on chain
            assert (
                check_deterministic_factory_deployment(
                    eth_rpc=self._eth_rpc, fork=self._fork
                )
                is not None
            ), "Deployment contract code is not found"

            # Deploy the actual contract.
            max_code_size = self._fork.max_code_size()
            if len(deploy_code) > max_code_size:
                raise ValueError(
                    f"code too large: {len(deploy_code)} > {max_code_size}"
                )
            max_initcode_size = self._fork.max_initcode_size()
            if len(initcode) > max_initcode_size:
                raise ValueError(
                    f"initcode too large {len(initcode)} > {max_initcode_size}"
                )
            deploy_gas_limit = (
                gas_costs.G_TRANSACTION + gas_costs.G_TRANSACTION_CREATE
            )
            deploy_gas_limit += (
                len(deploy_code) * gas_costs.G_CODE_DEPOSIT_BYTE
            )
            deploy_gas_limit += memory_expansion_gas_calculator(
                new_bytes=len(initcode)
            )
            deploy_gas_limit += calldata_gas_calculator(data=initcode)
            deploy_gas_limit = deploy_gas_limit * 2
            tx_gas_limit_cap = self._fork.transaction_gas_limit_cap()
            if tx_gas_limit_cap and deploy_gas_limit > tx_gas_limit_cap:
                raise ValueError(
                    f"deterministic deploy gas limit exceeds the transaction gas limit cap: {deploy_gas_limit} > {tx_gas_limit_cap}"
                )
            deploy_tx = self._add_pending_tx(
                action="deterministic_deploy_contract",
                target=label,
                to=DETERMINISTIC_FACTORY_ADDRESS,
                data=Bytes(salt) + Bytes(initcode),
                gas_limit=deploy_gas_limit,
                value=0,
            )
            logger.info(
                f"Contract deployment tx created (label={label}): "
                f"tx_nonce={deploy_tx.nonce}, gas_limit={deploy_gas_limit}, "
                f"code_size={len(deploy_code)} bytes, initcode_size={len(initcode)} bytes"
            )

            logger.debug(
                f"Contract will be deployed at {contract_address} "
                f"(label={label}, tx_index={len(self._pending_txs) - 1})"
            )

            self._deployed_contracts.append((contract_address, deploy_code))

        balance = self._eth_rpc.get_balance(contract_address)
        nonce = self._eth_rpc.get_transaction_count(contract_address)
        super().__setitem__(
            contract_address,
            Account(
                nonce=nonce,
                balance=balance,
                code=deploy_code,
                storage={},
            ),
        )

        contract_address.label = label
        return contract_address

    def deploy_contract(
        self,
        code: BytesConvertible,
        *,
        storage: Storage | StorageRootType | None = None,
        balance: NumberConvertible = 0,
        nonce: NumberConvertible = 1,
        address: Address | None = None,
        label: str | None = None,
        stub: str | None = None,
    ) -> Address:
        """Deploy a contract to the allocation."""
        if storage is None:
            storage = {}
        assert address is None, "address parameter is not supported"

        gas_costs = self._fork.gas_costs()
        memory_expansion_gas_calculator = (
            self._fork.memory_expansion_gas_calculator()
        )
        calldata_gas_calculator = self._fork.calldata_gas_calculator(
            block_number=0, timestamp=0
        )

        if not isinstance(storage, Storage):
            storage = Storage(storage)  # type: ignore

        if stub is not None and self._address_stubs is not None:
            if stub not in self._address_stubs:
                raise ValueError(
                    f"Stub name {stub} not found in address stubs"
                )
            contract_address = self._address_stubs[stub]
            logger.info(
                f"Using address stub '{stub}' at {contract_address} "
                f"(label={label})"
            )
            code = self._eth_rpc.get_code(contract_address)
            if code == b"":
                raise ValueError(
                    f"Stub {stub} at {contract_address} has no code"
                )
            balance = self._eth_rpc.get_balance(contract_address)
            nonce = self._eth_rpc.get_transaction_count(contract_address)
            logger.debug(
                f"Stub contract {contract_address}: balance={balance / 10**18:.18f} ETH, "
                f"nonce={nonce}, code_size={len(code)} bytes"
            )
            super().__setitem__(
                contract_address,
                Account(
                    nonce=nonce,
                    balance=balance,
                    code=code,
                    storage={},
                ),
            )
            return contract_address

        initcode_prefix = Bytecode()

        deploy_gas_limit = (
            gas_costs.G_TRANSACTION + gas_costs.G_TRANSACTION_CREATE
        )

        if len(storage.root) > 0:
            initcode_prefix += sum(
                Op.SSTORE(key, value) for key, value in storage.root.items()
            )
            deploy_gas_limit += len(storage.root) * 22_600

        assert isinstance(code, Bytecode), (
            f"incompatible code type: {type(code)}"
        )
        code = self.code_pre_processor(code)

        max_code_size = self._fork.max_code_size()
        if len(code) > max_code_size:
            raise ValueError(f"code too large: {len(code)} > {max_code_size}")

        deploy_gas_limit += len(code) * gas_costs.G_CODE_DEPOSIT_BYTE

        prepared_initcode = Initcode(
            deploy_code=code, initcode_prefix=initcode_prefix
        )
        deploy_gas_limit += memory_expansion_gas_calculator(
            new_bytes=len(bytes(prepared_initcode))
        )

        max_initcode_size = self._fork.max_initcode_size()
        if len(prepared_initcode) > max_initcode_size:
            raise ValueError(
                f"initcode too large {len(prepared_initcode)} > {max_initcode_size}"
            )

        deploy_gas_limit += calldata_gas_calculator(data=prepared_initcode)

        deploy_gas_limit = deploy_gas_limit * 2
        tx_gas_limit_cap = self._fork.transaction_gas_limit_cap()
        if tx_gas_limit_cap and deploy_gas_limit > tx_gas_limit_cap:
            raise ValueError(
                f"deploy gas limit exceeds the transaction gas limit cap: {deploy_gas_limit} > {tx_gas_limit_cap}"
            )

        deploy_tx = self._add_pending_tx(
            action="deploy_contract",
            target=label,
            to=None,
            data=prepared_initcode,
            value=balance,
            gas_limit=deploy_gas_limit,
        )
        logger.info(
            f"Contract deployment tx created (label={label}): "
            f"tx_nonce={deploy_tx.nonce}, gas_limit={deploy_gas_limit}, "
            f"code_size={len(code)} bytes, initcode_size={len(prepared_initcode)} bytes, "
            f"balance={Number(balance) / 10**18:.18f} ETH, storage_slots={len(storage.root)}"
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

        super().__setitem__(
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

    def fund_eoa(
        self,
        amount: NumberConvertible | None = None,
        label: str | None = None,
        storage: Storage | StorageRootType | None = None,
        delegation: Address | Literal["Self"] | None = None,
        nonce: NumberConvertible | None = None,
    ) -> EOA:
        """
        Add a previously unused EOA to the pre-alloc with the balance specified
        by `amount`.
        """
        assert nonce is None, "nonce parameter is not supported for execute"
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
                    f"Deploying storage contract for EOA {eoa} with {len(storage)} storage slots"
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
                    f"Storage contract deployed at {sstore_address} for EOA {eoa}"
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
        super().__setitem__(eoa, account)
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

    def fund_address(
        self,
        address: Address,
        amount: NumberConvertible,
        *,
        minimum_balance: bool = False,
    ) -> None:
        """
        Fund an address with a given amount.

        If the address is already present in the pre-alloc the amount will be
        added to its existing balance.
        """
        current_balance = self._eth_rpc.get_balance(address)
        fund_amount = int(Number(amount))

        if minimum_balance:
            if current_balance >= fund_amount:
                logger.info(
                    f"Skipping funding for address {address} (label={address.label}): "
                    f"current balance {current_balance / 10**18:.18f} ETH >= "
                    f"minimum {fund_amount / 10**18:.18f} ETH"
                )
                if address in self:
                    account = self[address]
                    if account is not None:
                        account.balance = ZeroPaddedHexNumber(current_balance)
                else:
                    super().__setitem__(
                        address, Account(balance=current_balance)
                    )
                return
            logger.debug(
                f"Funding address to minimum balance {address} (label={address.label}): "
                f"{fund_amount / 10**18:.18f} ETH"
            )
            self._add_pending_tx(
                action="fund_address",
                target=address.label,
                to=address,
                value=fund_amount - current_balance,
            )
            new_balance = fund_amount
        else:
            logger.debug(
                f"Funding address {address} (label={address.label}): "
                f"{fund_amount / 10**18:.18f} ETH"
            )
            self._add_pending_tx(
                action="fund_address",
                target=address.label,
                to=address,
                value=amount,
            )
            new_balance = current_balance + fund_amount

        if address in self:
            account = self[address]
            if account is not None:
                account.balance = ZeroPaddedHexNumber(new_balance)
                logger.debug(
                    f"Updated balance for existing address {address}: "
                    f"{current_balance / 10**18:.18f} ETH -> {new_balance / 10**18:.18f} ETH"
                )
            else:
                super().__setitem__(address, Account(balance=new_balance))
        else:
            super().__setitem__(address, Account(balance=new_balance))

        logger.info(
            f"Address {address} funding tx created (label={address.label}): "
            f"{Number(amount) / 10**18:.18f} ETH"
        )

    def empty_account(self) -> Address:
        """
        Add a previously unused account guaranteed to be empty to the
        pre-alloc.

        This ensures the account has:
        - Zero balance
        - Zero nonce
        - No code
        - No storage

        This is different from precompiles or system contracts. The function
        does not send any transactions, ensuring that the account remains
        "empty."

        Returns:
            Address: The address of the created empty account.

        """
        eoa = next(self._eoa_iterator)
        logger.debug(f"Creating empty account at {eoa}")

        super().__setitem__(
            eoa,
            Account(
                nonce=0,
                balance=0,
            ),
        )
        return Address(eoa)

    def minimum_balance_for_pending_transactions(
        self,
        sender_balances: Dict[Address, int],
        gas_price: int,
        max_fee_per_gas: int,
        max_priority_fee_per_gas: int,
        max_fee_per_blob_gas: int,
    ) -> Tuple[int, int]:
        """
        Calculate the minimum balance required by the sender to send all pending
        transactions.
        """
        minimum_balance = 0
        gas_consumption = 0
        for tx in self._pending_txs:
            if tx.value is None:
                # WARN: This currently fails if there's an account with `pre.fund_eoa()` that
                # never sends a transaction during the test.
                if tx.to not in sender_balances:
                    error_message = (
                        "Sender balance must be set before sending:"
                        f"\nTransaction: {tx.model_dump_json(indent=2)}"
                    )
                    if tx.metadata is not None:
                        error_message += f"\nMetadata: {tx.metadata.model_dump_json(indent=2)}"
                    logger.error(error_message)
                    raise ValueError(error_message)
                sender_balance = sender_balances[tx.to]
                logger.info(
                    f"Deferred EOA balance for {tx.to} set to {sender_balance / 10**18:.18f} ETH"
                )
                tx.value = HexNumber(sender_balance)
            tx.set_gas_price(
                gas_price=gas_price,
                max_fee_per_gas=max_fee_per_gas,
                max_priority_fee_per_gas=max_priority_fee_per_gas,
                max_fee_per_blob_gas=max_fee_per_blob_gas,
            )
            gas_consumption += tx.gas_limit
            minimum_balance += tx.signer_minimum_balance(fork=self._fork)
        return minimum_balance + gas_consumption * gas_price, gas_consumption

    def send_pending_transactions(self) -> List[TransactionByHashResponse]:
        """Send all pending transactions and wait for them to be included."""
        logger.info(
            f"Sending {len(self._pending_txs)} pending transactions "
            f"(deployed_contracts={len(self._deployed_contracts)}, "
            f"funded_eoas={len(self._funded_eoa)})"
        )
        transaction_batches: List[List[PendingTransaction]] = []
        last_tx_batch: List[PendingTransaction] = []
        MAX_TXS_PER_BATCH = 100
        for tx in self._pending_txs:
            assert tx.value is not None, (
                "Transaction value must be set before sending them to the RPC."
            )
            if len(last_tx_batch) >= MAX_TXS_PER_BATCH:
                transaction_batches.append(last_tx_batch)
                last_tx_batch = []
            last_tx_batch.append(tx)
        if last_tx_batch:
            transaction_batches.append(last_tx_batch)

        responses: List[TransactionByHashResponse] = []
        for tx_batch in transaction_batches:
            txs = [tx.with_signature_and_sender() for tx in tx_batch]
            tx_hashes = self._eth_rpc.send_transactions(txs)
            logger.info(
                f"Sent {len(tx_hashes)} transactions: {[str(h) for h in tx_hashes[:5]]}"
                + (
                    f" and {len(tx_hashes) - 5} more"
                    if len(tx_hashes) > 5
                    else ""
                )
            )
            logger.info(
                f"Waiting for {len(tx_batch)} transactions to be included in blocks"
            )
            responses += self._eth_rpc.wait_for_transactions(tx_batch)
            logger.info(
                f"All {len(responses)} transactions confirmed in blocks"
            )
        for response in responses:
            logger.debug(f"Transaction response: {response.model_dump_json()}")
        return responses


@pytest.fixture(autouse=True, scope="function")
def pre(
    fork: Fork,
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
    logger.info(
        f"Starting cleanup phase: refunding {len(pre._funded_eoa)} funded EOAs"
    )
    refund_txs = []
    skipped_refunds = 0
    error_refunds = 0
    for idx, eoa in enumerate(pre._funded_eoa):
        remaining_balance = eth_rpc.get_balance(eoa)
        eoa.nonce = Number(eth_rpc.get_transaction_count(eoa))
        refund_gas_limit = 21_000
        tx_cost = refund_gas_limit * max_fee_per_gas
        if remaining_balance < tx_cost:
            logger.debug(
                f"Skipping refund for EOA {eoa} (label={eoa.label}): "
                f"insufficient balance {remaining_balance / 10**18:.18f} ETH < "
                f"transaction cost {tx_cost / 10**18:.18f} ETH"
            )
            skipped_refunds += 1
            continue
        refund_value = remaining_balance - tx_cost
        logger.debug(
            f"Preparing refund transaction for EOA {eoa} (label={eoa.label}): "
            f"{refund_value / 10**18:.18f} ETH (remaining: {remaining_balance / 10**18:.18f} ETH, "
            f"cost: {tx_cost / 10**18:.18f} ETH)"
        )
        refund_tx = Transaction(
            sender=eoa,
            to=worker_key,
            gas_limit=21_000,
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
        try:
            logger.info(
                f"Sending refund transaction for EOA {eoa}: {refund_tx.hash}"
            )
            refund_tx_hash = eth_rpc.send_transaction(refund_tx)
            logger.info(f"Refund transaction sent: {refund_tx_hash}")
            refund_txs.append(refund_tx)
        except Exception as e:
            eoa_key = eoa.key
            logger.error(
                f"Error sending refund transaction for EOA {eoa}: {e}."
            )
            if eoa_key is not None:
                logger.info(
                    f"Retrieve funds manually from EOA {eoa} "
                    f"using private key {eoa_key.hex()}."
                )
            error_refunds += 1
            continue
    if refund_txs:
        logger.info(
            f"Waiting for {len(refund_txs)} refund transactions "
            f"({skipped_refunds} skipped due to insufficient balance, "
            f"{error_refunds} errored)"
        )
        eth_rpc.wait_for_transactions(refund_txs)
        logger.info(f"All {len(refund_txs)} refund transactions confirmed")
    else:
        logger.info(
            f"No refund transactions to send ({skipped_refunds} EOAs skipped "
            f"due to insufficient balance, {error_refunds} errored)"
        )
