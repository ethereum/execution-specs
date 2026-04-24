"""
Corruption catalog for EIP-7928 Block Access Lists.

Derives the full set of *corruption cases* from a valid
`BlockAccessListExpectation`. Each case bundles:

  - a stable ``id`` for pytest parametrization,
  - a ``modifier`` that, when applied to the real t8n-produced BAL at
    fill time, yields a corrupted variant,
  - the ``expected_exception`` the client must raise on that variant.

The catalog is pure: it never touches a real BAL and has no side
effects. Higher-level nibbles wire these cases into pytest.

## ID format

::

    <address_hex>__<prefix>_<field>   — account-targeted
    <prefix>_<field>                  — BAL-level

``<address_hex>`` is ``str(address)`` — the canonical 0x-prefixed
lowercase hex form. Using the address directly makes IDs independent of
dict iteration order or any external labeling scheme.

## Prefixes

- ``corrupt_``   — XOR-flip an existing write value (Correctness).
- ``omit_``      — remove an access-list or the whole account
  (Exactness).
- ``duplicate_`` — repeat an existing access (Exactness).
- ``phantom_``   — inject an entry execution never produced (Exactness).
- ``swap_``      — swap a pair at account- or index-level (Sequence).
"""

from typing import Callable, List, NamedTuple

from execution_testing.exceptions import BlockException

from .expectations import BlockAccessListExpectation
from .t8n import BlockAccessList

Modifier = Callable[[BlockAccessList], BlockAccessList]


class CorruptionCase(NamedTuple):
    """
    One corruption derived from a valid BAL expectation.

    Fields
    ------
    id
        Stable string for pytest parametrization. See module docstring
        for the naming convention.
    modifier
        Callable that, applied to the real t8n-produced BAL at fill
        time, yields the corrupted variant.
    expected_exception
        The ``BlockException`` the client must raise when verifying the
        corrupted block.
    """

    id: str
    modifier: Modifier
    expected_exception: BlockException


def enumerate_corruptions(
    expectation: BlockAccessListExpectation,
) -> List[CorruptionCase]:
    r"""
    Return every corruption case derivable from ``expectation``.

    Emits cases along three axes:

    - **Correctness** — ``corrupt_<field>`` per existing change.
    - **Exactness** — ``omit_*``, ``duplicate_*``, ``phantom_*``.
    - **Sequence** — ``swap_accounts`` and ``swap_indices`` where
      applicable.

    The total count is:

    .. math::

        N = 2C + R + K + 6A + 1 + \\alpha + \\beta

    where :math:`A` = accounts, :math:`C` = total changes, :math:`R` =
    total reads, :math:`K` = populated access-lists, :math:`\\alpha` =
    1 if :math:`A \\geq 2` else 0, :math:`\\beta` = 1 if there are
    :math:`\\geq 2` distinct ``block_access_index`` values else 0.

    See the module docstring for the ID format.
    """
    raise NotImplementedError(
        "enumerate_corruptions is not yet implemented; "
    )
