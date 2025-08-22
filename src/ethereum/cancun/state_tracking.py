from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union

from ethereum_types.bytes import Bytes32
from ethereum_types.numeric import U256

from .fork_types import Account, Address

# State access types for tracking
ACCOUNT_READ = "account_read"
ACCOUNT_WRITE = "account_write"
STORAGE_READ = "storage_read"  
STORAGE_WRITE = "storage_write"


@dataclass
class StateAccess:
    """Record of a single state access for proof generation."""
    access_type: str
    address: Address
    key: Optional[Bytes32] = None
    value_before: Optional[Union[Account, U256]] = None
    value_after: Optional[Union[Account, U256]] = None


@dataclass
class StateTracker:
    """Tracks state access for merkle proof generation."""
    accesses: List[StateAccess] = field(default_factory=list)
    main_trie_accessed_keys: Set[Address] = field(default_factory=set)
    storage_accessed_keys: Dict[Address, Set[Bytes32]] = field(default_factory=dict)
    track_reads: bool = True
    track_writes: bool = True


def enable_state_tracking(
    state, 
    track_reads: bool = True, 
    track_writes: bool = True
) -> None:
    """
    Enable state tracking on a State object.
    
    Parameters
    ----------
    state : State
        The state to enable tracking on
    track_reads : bool
        Whether to track read operations
    track_writes : bool
        Whether to track write operations
    """
    state._state_tracker = StateTracker(
        track_reads=track_reads,
        track_writes=track_writes
    )


def disable_state_tracking(state) -> None:
    """
    Disable state tracking on a State object.
    
    Parameters
    ----------
    state : State
        The state to disable tracking on
    """
    state._state_tracker = None


def log_state_access(
    state,
    access_type: str,
    address: Address,
    key: Optional[Bytes32] = None,
    value_before: Optional[Union[Account, U256]] = None,
    value_after: Optional[Union[Account, U256]] = None,
) -> None:
    """
    Log a state access if tracking is enabled.
    
    Parameters
    ----------
    state : State
        The state (with potential tracker)
    access_type : str
        Type of access (ACCOUNT_READ, ACCOUNT_WRITE, etc.)
    address : Address
        Address being accessed
    key : Optional[Bytes32]
        Storage key (for storage operations)
    value_before : Optional[Union[Account, U256]]
        Value before the operation
    value_after : Optional[Union[Account, U256]]
        Value after the operation
    """
    if state._state_tracker is None:
        return
    
    tracker = state._state_tracker
    access = StateAccess(
        access_type=access_type,
        address=address,
        key=key,
        value_before=value_before,
        value_after=value_after,
    )
    tracker.accesses.append(access)
    
    if access_type in [ACCOUNT_READ, ACCOUNT_WRITE]:
        tracker.main_trie_accessed_keys.add(address)
    elif access_type in [STORAGE_READ, STORAGE_WRITE]:
        if address not in tracker.storage_accessed_keys:
            tracker.storage_accessed_keys[address] = set()
        if key is not None:
            tracker.storage_accessed_keys[address].add(key)

# Dummy method
def generate_merkle_proof_requests(state) -> Tuple[List[Address], List[Tuple[Address, Bytes32]]]:
    """
    Generate lists of proof requests needed for all tracked accesses.
    
    Parameters
    ----------
    state : State
        The state containing tracking logs
        
    Returns
    -------
    account_proofs : List[Address]
        List of addresses needing account proofs
    storage_proofs : List[Tuple[Address, Bytes32]]
        List of (address, storage_key) tuples needing storage proofs
    """
    return [], []
