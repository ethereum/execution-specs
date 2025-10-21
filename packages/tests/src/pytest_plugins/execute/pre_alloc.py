"""Pre-allocation fixtures using for test filling."""

from itertools import count
from pathlib import Path
from random import randint
from typing import Any, Dict, Generator, Iterator, List, Literal, Self, Tuple

import pytest
import yaml
from pydantic import PrivateAttr

from ethereum_test_base_types import (
    Bytes,
    EthereumTestRootModel,
    Number,
    StorageRootType,
    ZeroPaddedHexNumber,
)
from ethereum_test_base_types.conversions import (
    BytesConvertible,
    FixedSizeBytesConvertible,
    NumberConvertible,
)
from ethereum_test_forks import Fork
from ethereum_test_rpc import EthRPC
from ethereum_test_rpc.rpc_types import TransactionByHashResponse
from ethereum_test_tools import (
    EOA,
    Account,
    Address,
    AuthorizationTuple,
    Initcode,
    Storage,
    Transaction,
)
from ethereum_test_tools import Alloc as BaseAlloc
from ethereum_test_tools import Opcodes as Op
from ethereum_test_types import ChainConfig, TransactionTestMetadata
from ethereum_test_types.eof.v1 import Container
from ethereum_test_vm import Bytecode, EVMCodeType, Opcodes

MAX_BYTECODE_SIZE = 24576
MAX_INITCODE_SIZE = MAX_BYTECODE_SIZE * 2


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
        "--evm-code-type",
        action="store",
        dest="evm_code_type",
        default=None,
        type=EVMCodeType,
        choices=list(EVMCodeType),
        help="Type of EVM code to deploy in each test by default.",
    )
    pre_alloc_group.addoption(
        "--eoa-fund-amount-default",
        action="store",
        dest="eoa_fund_amount_default",
        default=10**18,
        type=int,
        help="The default amount of wei to fund each EOA in each test with.",
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
    return request.config.getoption("address_stubs", None)


@pytest.fixture(scope="session")
def skip_cleanup(request: pytest.FixtureRequest) -> bool:
    """Return whether to skip cleanup phase after each test."""
    return request.config.getoption("skip_cleanup")


@pytest.fixture(scope="session")
def eoa_iterator(request: pytest.FixtureRequest) -> Iterator[EOA]:
    """Return an iterator that generates EOAs."""
    eoa_start = request.config.getoption("eoa_iterator_start")
    print(f"Starting EOA index: {hex(eoa_start)}")
    return iter(EOA(key=i, nonce=0) for i in count(start=eoa_start))


class Alloc(BaseAlloc):
    """A custom class that inherits from the original Alloc class."""

    _fork: Fork = PrivateAttr()
    _sender: EOA = PrivateAttr()
    _eth_rpc: EthRPC = PrivateAttr()
    _txs: List[Transaction] = PrivateAttr(default_factory=list)
    _deployed_contracts: List[Tuple[Address, Bytes]] = PrivateAttr(
        default_factory=list
    )
    _funded_eoa: List[EOA] = PrivateAttr(default_factory=list)
    _evm_code_type: EVMCodeType | None = PrivateAttr(None)
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
        eoa_fund_amount_default: int,
        evm_code_type: EVMCodeType | None = None,
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
        self._evm_code_type = evm_code_type
        self._chain_id = chain_id
        self._eoa_fund_amount_default = eoa_fund_amount_default
        self._node_id = node_id
        self._address_stubs = address_stubs or AddressStubs(root={})

    # always refresh _sender nonce from RPC ("pending") before building tx
    def _refresh_sender_nonce(self) -> None:
        """
        Synchronize self._sender.nonce with the node's view.
        Prefer 'pending' to account for in-flight transactions.
        """
        try:
            rpc_nonce = self._eth_rpc.get_transaction_count(
                self._sender, block_number="pending"
            )
        except TypeError:
            # If EthRPC.get_transaction_count has no 'block' kwarg
            rpc_nonce = self._eth_rpc.get_transaction_count(self._sender)
        self._sender.nonce = Number(rpc_nonce)

    def __setitem__(
        self,
        address: Address | FixedSizeBytesConvertible,
        account: Account | None,
    ) -> None:
        """Set account associated with an address."""
        raise ValueError(
            "Tests are not allowed to set pre-alloc items in execute mode"
        )

    def code_pre_processor(
        self,
        code: Bytecode | Container,
        *,
        evm_code_type: EVMCodeType | None,
    ) -> Bytecode | Container:
        """Pre-processes the code before setting it."""
        if evm_code_type is None:
            evm_code_type = self._evm_code_type
        if evm_code_type == EVMCodeType.EOF_V1:
            if not isinstance(code, Container):
                if isinstance(code, Bytecode) and not code.terminating:
                    return Container.Code(code + Opcodes.STOP)
                return Container.Code(code)
        return code

    def deploy_contract(
        self,
        code: BytesConvertible,
        *,
        storage: Storage | StorageRootType | None = None,
        balance: NumberConvertible = 0,
        nonce: NumberConvertible = 1,
        address: Address | None = None,
        evm_code_type: EVMCodeType | None = None,
        label: str | None = None,
        stub: str | None = None,
    ) -> Address:
        """Deploy a contract to the allocation."""
        if storage is None:
            storage = {}
        assert address is None, "address parameter is not supported"

        if not isinstance(storage, Storage):
            storage = Storage(storage)  # type: ignore

        if stub is not None and self._address_stubs is not None:
            if stub not in self._address_stubs:
                raise ValueError(
                    f"Stub name {stub} not found in address stubs"
                )
            contract_address = self._address_stubs[stub]
            code = self._eth_rpc.get_code(contract_address)
            if code == b"":
                raise ValueError(
                    f"Stub {stub} at {contract_address} has no code"
                )
            balance = self._eth_rpc.get_balance(contract_address)
            nonce = self._eth_rpc.get_transaction_count(contract_address)
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

        deploy_gas_limit = 21_000 + 32_000

        if len(storage.root) > 0:
            initcode_prefix += sum(
                Op.SSTORE(key, value) for key, value in storage.root.items()
            )
            deploy_gas_limit += len(storage.root) * 22_600

        assert isinstance(code, Bytecode) or isinstance(code, Container), (
            f"incompatible code type: {type(code)}"
        )
        code = self.code_pre_processor(code, evm_code_type=evm_code_type)

        assert len(code) <= MAX_BYTECODE_SIZE, (
            f"code too large: {len(code)} > {MAX_BYTECODE_SIZE}"
        )

        deploy_gas_limit += len(bytes(code)) * 200

        initcode: Bytecode | Container

        if evm_code_type == EVMCodeType.EOF_V1:
            assert isinstance(code, Container)
            initcode = Container.Init(
                deploy_container=code, initcode_prefix=initcode_prefix
            )
        else:
            initcode = Initcode(
                deploy_code=code, initcode_prefix=initcode_prefix
            )
            memory_expansion_gas_calculator = (
                self._fork.memory_expansion_gas_calculator()
            )
            deploy_gas_limit += memory_expansion_gas_calculator(
                new_bytes=len(bytes(initcode))
            )

        assert len(initcode) <= MAX_INITCODE_SIZE, (
            f"initcode too large {len(initcode)} > {MAX_INITCODE_SIZE}"
        )

        calldata_gas_calculator = self._fork.calldata_gas_calculator(
            block_number=0, timestamp=0
        )
        deploy_gas_limit += calldata_gas_calculator(data=initcode)

        # Limit the gas limit
        deploy_gas_limit = min(deploy_gas_limit * 2, 30_000_000)
        print(f"Deploying contract with gas limit: {deploy_gas_limit}")

        self._refresh_sender_nonce()

        deploy_tx = Transaction(
            sender=self._sender,
            to=None,
            data=initcode,
            value=balance,
            gas_limit=deploy_gas_limit,
        ).with_signature_and_sender()
        deploy_tx.metadata = TransactionTestMetadata(
            test_id=self._node_id,
            phase="setup",
            action="deploy_contract",
            target=label,
            tx_index=len(self._txs),
        )
        self._eth_rpc.send_transaction(deploy_tx)
        self._txs.append(deploy_tx)

        contract_address = deploy_tx.created_contract
        self._deployed_contracts.append((contract_address, Bytes(code)))

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
        storage: Storage | None = None,
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
        # Send a transaction to fund the EOA
        if amount is None:
            amount = self._eoa_fund_amount_default

        fund_tx: Transaction | None = None
        if delegation is not None or storage is not None:
            if storage is not None:
                sstore_address = self.deploy_contract(
                    code=(
                        sum(
                            Op.SSTORE(key, value)
                            for key, value in storage.root.items()
                        )
                        + Op.STOP
                    )
                )

                self._refresh_sender_nonce()

                set_storage_tx = Transaction(
                    sender=self._sender,
                    to=eoa,
                    authorization_list=[
                        AuthorizationTuple(
                            chain_id=self._chain_id,
                            address=sstore_address,
                            nonce=eoa.nonce,
                            signer=eoa,
                        ),
                    ],
                    gas_limit=100_000,
                ).with_signature_and_sender()
                eoa.nonce = Number(eoa.nonce + 1)
                set_storage_tx.metadata = TransactionTestMetadata(
                    test_id=self._node_id,
                    phase="setup",
                    action="eoa_storage_set",
                    target=label,
                    tx_index=len(self._txs),
                )
                self._eth_rpc.send_transaction(set_storage_tx)
                self._txs.append(set_storage_tx)

            self._refresh_sender_nonce()

            if delegation is not None:
                if (
                    not isinstance(delegation, Address)
                    and delegation == "Self"
                ):
                    delegation = eoa
                # TODO: This tx has side-effects on the EOA state because of
                # the delegation
                fund_tx = Transaction(
                    sender=self._sender,
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
                ).with_signature_and_sender()
                eoa.nonce = Number(eoa.nonce + 1)
            else:
                fund_tx = Transaction(
                    sender=self._sender,
                    to=eoa,
                    value=amount,
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
                ).with_signature_and_sender()
                eoa.nonce = Number(eoa.nonce + 1)

        else:
            if Number(amount) > 0:
                self._refresh_sender_nonce()

                fund_tx = Transaction(
                    sender=self._sender,
                    to=eoa,
                    value=amount,
                ).with_signature_and_sender()

        if fund_tx is not None:
            fund_tx.metadata = TransactionTestMetadata(
                test_id=self._node_id,
                phase="setup",
                action="fund_eoa",
                target=label,
                tx_index=len(self._txs),
            )
            self._eth_rpc.send_transaction(fund_tx)
            self._txs.append(fund_tx)
        super().__setitem__(
            eoa,
            Account(
                nonce=eoa.nonce,
                balance=amount,
            ),
        )
        self._funded_eoa.append(eoa)
        return eoa

    def fund_address(
        self, address: Address, amount: NumberConvertible
    ) -> None:
        """
        Fund an address with a given amount.

        If the address is already present in the pre-alloc the amount will be
        added to its existing balance.
        """
        self._refresh_sender_nonce()

        fund_tx = Transaction(
            sender=self._sender,
            to=address,
            value=amount,
        ).with_signature_and_sender()
        fund_tx.metadata = TransactionTestMetadata(
            test_id=self._node_id,
            phase="setup",
            action="fund_address",
            target=address.label,
            tx_index=len(self._txs),
        )
        self._eth_rpc.send_transaction(fund_tx)
        self._txs.append(fund_tx)
        if address in self:
            account = self[address]
            if account is not None:
                current_balance = account.balance or 0
                account.balance = ZeroPaddedHexNumber(
                    current_balance + Number(amount)
                )
                return

        super().__setitem__(address, Account(balance=amount))

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

        super().__setitem__(
            eoa,
            Account(
                nonce=0,
                balance=0,
            ),
        )
        return Address(eoa)

    def wait_for_transactions(self) -> List[TransactionByHashResponse]:
        """Wait for all transactions to be included in blocks."""
        return self._eth_rpc.wait_for_transactions(self._txs)


@pytest.fixture(autouse=True)
def evm_code_type(request: pytest.FixtureRequest) -> EVMCodeType:
    """Return default EVM code type for all tests (LEGACY)."""
    parameter_evm_code_type = request.config.getoption("evm_code_type")
    if parameter_evm_code_type is not None:
        assert type(parameter_evm_code_type) is EVMCodeType, (
            "Invalid EVM code type"
        )
        return parameter_evm_code_type
    return EVMCodeType.LEGACY


@pytest.fixture(scope="session")
def eoa_fund_amount_default(request: pytest.FixtureRequest) -> int:
    """Get the gas price for the funding transactions."""
    return request.config.option.eoa_fund_amount_default


@pytest.fixture(autouse=True, scope="function")
def pre(
    fork: Fork,
    sender_key: EOA,
    eoa_iterator: Iterator[EOA],
    eth_rpc: EthRPC,
    evm_code_type: EVMCodeType,
    chain_config: ChainConfig,
    eoa_fund_amount_default: int,
    default_gas_price: int,
    address_stubs: AddressStubs | None,
    skip_cleanup: bool,
    request: pytest.FixtureRequest,
) -> Generator[Alloc, None, None]:
    """Return default pre allocation for all tests (Empty alloc)."""
    # FIXME: Static tests don't have a fork so we need to get it from the node.
    actual_fork = fork
    if actual_fork is None:
        assert hasattr(request.node, "fork")
        actual_fork = request.node.fork

    # Record the starting balance of the sender
    sender_test_starting_balance = eth_rpc.get_balance(sender_key)

    # Prepare the pre-alloc
    pre = Alloc(
        fork=fork,
        sender=sender_key,
        eth_rpc=eth_rpc,
        eoa_iterator=eoa_iterator,
        evm_code_type=evm_code_type,
        chain_id=chain_config.chain_id,
        eoa_fund_amount_default=eoa_fund_amount_default,
        node_id=request.node.nodeid,
        address_stubs=address_stubs,
    )

    # Yield the pre-alloc for usage during the test
    yield pre

    if not skip_cleanup:
        # Refund all EOAs (regardless of whether the test passed or failed)
        refund_txs = []
        for idx, eoa in enumerate(pre._funded_eoa):
            remaining_balance = eth_rpc.get_balance(eoa)
            eoa.nonce = Number(eth_rpc.get_transaction_count(eoa))
            refund_gas_limit = 21_000
            tx_cost = refund_gas_limit * default_gas_price
            if remaining_balance < tx_cost:
                continue
            refund_tx = Transaction(
                sender=eoa,
                to=sender_key,
                gas_limit=21_000,
                gas_price=default_gas_price,
                value=remaining_balance - tx_cost,
            ).with_signature_and_sender()
            refund_tx.metadata = TransactionTestMetadata(
                test_id=request.node.nodeid,
                phase="cleanup",
                action="refund_from_eoa",
                target=eoa.label,
                tx_index=idx,
            )
            refund_txs.append(refund_tx)
        eth_rpc.send_wait_transactions(refund_txs)

    # Record the ending balance of the sender
    sender_test_ending_balance = eth_rpc.get_balance(sender_key)
    used_balance = sender_test_starting_balance - sender_test_ending_balance
    print(f"Used balance={used_balance / 10**18:.18f}")
