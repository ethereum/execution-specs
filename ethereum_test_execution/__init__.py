"""
Ethereum test execution package.
"""
from typing import Dict

from .base import BaseExecute, ExecuteFormat
from .transaction_post import TransactionPost

EXECUTE_FORMATS: Dict[str, ExecuteFormat] = {
    f.execute_format_name: f  # type: ignore
    for f in [
        TransactionPost,
    ]
}
__all__ = [
    "BaseExecute",
    "ExecuteFormat",
    "TransactionPost",
    "EXECUTE_FORMATS",
]
