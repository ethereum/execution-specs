"""
Reference Spec Classes
"""
from typing import Sequence, Type

from .git_reference_spec import GitReferenceSpec
from .reference_spec import ReferenceSpec

ReferenceSpecTypes: Sequence[Type[ReferenceSpec]] = [
    GitReferenceSpec,
]

__all__ = ("ReferenceSpec", "ReferenceSpecTypes")
