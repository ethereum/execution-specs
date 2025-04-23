"""Account structure of ethereum/tests fillers."""

from typing import Dict

from pydantic import BaseModel

from .common import CodeInFiller, ValueInFiller


class AccountInFiller(BaseModel):
    """Class that represents an account in filler."""

    balance: ValueInFiller
    code: CodeInFiller
    nonce: ValueInFiller
    storage: Dict[ValueInFiller, ValueInFiller]

    class Config:
        """Model Config."""

        extra = "forbid"
        arbitrary_types_allowed = True  # For CodeInFiller
