"""General transaction structure of ethereum/tests fillers."""

from typing import Any, Dict, Generator, List, Mapping

from pydantic import BaseModel, Field, field_validator, model_validator

from ethereum_test_base_types import Address, CamelModel, EthereumTestRootModel, Hash
from ethereum_test_exceptions import TransactionExceptionInstanceOrList
from ethereum_test_types import Transaction

from .common import (
    AccessListInFiller,
    AddressOrTagInFiller,
    CodeInFiller,
    HashOrTagInFiller,
    Tag,
    TagDependentData,
    TagDict,
    ValueInFiller,
)


class DataWithAccessList(CamelModel, TagDependentData):
    """Class that represents data with access list."""

    data: CodeInFiller
    access_list: List[AccessListInFiller] | None = None

    @field_validator("access_list", mode="before")
    def convert_keys_to_hash(cls, access_list):  # noqa: N805
        """Fix keys."""
        if access_list is None:
            return None
        for entry in access_list:
            if "storageKeys" in entry:
                entry["storageKeys"] = [
                    Hash(key, left_padding=True) for key in entry["storageKeys"]
                ]
        return access_list

    def tag_dependencies(self) -> Mapping[str, Tag]:
        """Get tag dependencies."""
        tag_dependencies: Dict[str, Tag] = {}
        if self.access_list is not None:
            for entry in self.access_list:
                tag_dependencies.update(entry.tag_dependencies())
        if self.data is not None and isinstance(self.data, CodeInFiller):
            tag_dependencies.update(self.data.tag_dependencies())
        return tag_dependencies

    @model_validator(mode="wrap")
    @classmethod
    def wrap_data_only(cls, data: Any, handler) -> "DataWithAccessList":
        """Wrap data only if it is not a dictionary."""
        if not isinstance(data, dict) and not isinstance(data, DataWithAccessList):
            data = {"data": data}
        return handler(data)


class LabeledDataIndex(BaseModel):
    """Represents an index with a label if any."""

    index: int
    label: str | None = None

    def __str__(self):
        """Transform into a string that can be part of a test name."""
        if self.label is not None:
            return self.label
        return f"{self.index}"


class LabeledDataList(EthereumTestRootModel):
    """Class that represents a list of labeled data."""

    root: List[DataWithAccessList]

    def __getitem__(self, label_or_index: int | str):
        """Get an item by label or index."""
        if isinstance(label_or_index, int):
            return self.root[label_or_index]
        if isinstance(label_or_index, str):
            for item in self.root:
                if item.data.label == label_or_index:
                    return item
        raise KeyError(f"Label/index {label_or_index} not found in data indexes")

    def __contains__(self, label_or_index: int | str):
        """Return True if the LabeledDataList contains the given label/index."""
        if isinstance(label_or_index, int):
            return label_or_index < len(self.root)
        if isinstance(label_or_index, str):
            for item in self.root:
                if item.data.label == label_or_index:
                    return True
        return False

    def __len__(self):
        """Return the length of the list."""
        return len(self.root)

    def __iter__(self) -> Generator[LabeledDataIndex, None, None]:  # type: ignore
        """Return the iterator of the root list."""
        for i, item in enumerate(self.root):
            labeled_data_index = LabeledDataIndex(index=i)
            if item.data.label is not None:
                labeled_data_index.label = item.data.label
            yield labeled_data_index


class GeneralTransactionInFiller(BaseModel, TagDependentData):
    """Class that represents general transaction in filler."""

    data: LabeledDataList
    gas_limit: List[ValueInFiller] = Field(..., alias="gasLimit")
    gas_price: ValueInFiller | None = Field(None, alias="gasPrice")
    nonce: ValueInFiller | None
    to: AddressOrTagInFiller | None
    value: List[ValueInFiller]
    secret_key: HashOrTagInFiller = Field(..., alias="secretKey")

    max_fee_per_gas: ValueInFiller | None = Field(None, alias="maxFeePerGas")
    max_priority_fee_per_gas: ValueInFiller | None = Field(None, alias="maxPriorityFeePerGas")

    max_fee_per_blob_gas: ValueInFiller | None = Field(None, alias="maxFeePerBlobGas")
    blob_versioned_hashes: List[Hash] | None = Field(None, alias="blobVersionedHashes")

    class Config:
        """Model Config."""

        extra = "forbid"

    def tag_dependencies(self) -> Mapping[str, Tag]:
        """Get tag dependencies."""
        tag_dependencies = {}
        if self.data:
            for idx in self.data:
                data = self.data[idx.index]
                tag_dependencies.update(data.tag_dependencies())
        if self.to is not None and isinstance(self.to, Tag):
            tag_dependencies[self.to.name] = self.to
        if self.secret_key is not None and isinstance(self.secret_key, Tag):
            tag_dependencies[self.secret_key.name] = self.secret_key
        return tag_dependencies

    @field_validator("to", mode="before")
    def check_single_key(cls, to):  # noqa: N805
        """Creation transaction."""
        if to == "":
            to = None
        return to

    @model_validator(mode="after")
    def check_fields(self) -> "GeneralTransactionInFiller":
        """Validate all fields are set."""
        if self.gas_price is None:
            if self.max_fee_per_gas is None or self.max_priority_fee_per_gas is None:
                raise ValueError(
                    "If `gasPrice` is not set,"
                    " `maxFeePerGas` and `maxPriorityFeePerGas` must be set!"
                )
        return self

    def get_transaction(
        self,
        tags: TagDict,
        d: int,
        g: int,
        v: int,
        exception: TransactionExceptionInstanceOrList | None,
    ) -> Transaction:
        """Get the transaction."""
        data_box = self.data[d]
        kwargs: Dict[str, Any] = {}
        if self.to is None:
            kwargs["to"] = None
        elif isinstance(self.to, Tag):
            kwargs["to"] = self.to.resolve(tags)
        else:
            kwargs["to"] = Address(self.to)

        kwargs["data"] = data_box.data.compiled(tags)
        if data_box.access_list is not None:
            kwargs["access_list"] = [entry.resolve(tags) for entry in data_box.access_list]

        kwargs["gas_limit"] = self.gas_limit[g]

        if isinstance(self.secret_key, Tag):
            sender = self.secret_key.resolve(tags)
            kwargs["secret_key"] = sender.key
        else:
            kwargs["secret_key"] = self.secret_key

        if self.value[v] > 0:
            kwargs["value"] = self.value[v]
        if self.gas_price is not None:
            kwargs["gas_price"] = self.gas_price
        if self.nonce is not None:
            kwargs["nonce"] = self.nonce
        if self.max_fee_per_gas is not None:
            kwargs["max_fee_per_gas"] = self.max_fee_per_gas
        if self.max_priority_fee_per_gas is not None:
            kwargs["max_priority_fee_per_gas"] = self.max_priority_fee_per_gas
        if self.max_fee_per_blob_gas is not None:
            kwargs["max_fee_per_blob_gas"] = self.max_fee_per_blob_gas
        if self.blob_versioned_hashes is not None:
            kwargs["blob_versioned_hashes"] = self.blob_versioned_hashes

        if exception is not None:
            kwargs["error"] = exception

        return Transaction(**kwargs)
