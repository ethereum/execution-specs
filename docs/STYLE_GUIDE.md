# EELS Style Guide

This document outlines style conventions for the Ethereum Execution Layer Specifications (EELS) that are not automatically enforced by Black formatter. These rules promote code clarity, consistency, and maintainability across the codebase.

## Function Naming

Function names should be **short, imperative verbs** in `snake_case` format. Follow [PEP 8](https://peps.python.org/pep-0008/#function-and-variable-names) naming conventions.

**Good:**
```python
def fetch_state(address: Address) -> Account:
    """Fetch account state from storage."""
    
def validate_block(block: Block) -> None:
    """Validate block structure and contents."""
    
def compute_hash(data: bytes) -> Hash32:
    """Compute hash of input data."""
```

**Avoid:**
```python
def do_fetch(address: Address) -> Account:  # Avoid "do_" prefixes
def get_the_state_data(address: Address) -> Account:  # Too verbose
def validateBlock(block: Block) -> None:  # Use snake_case, not camelCase
```

## Error Handling

Use **exceptions** for protocol-handled errors. Avoid sentinel return values for error conditions.

**Good:**
```python
def execute_transaction(tx: Transaction) -> Receipt:
    if tx.gas_limit < INTRINSIC_GAS:
        raise InsufficientGas("Gas limit too low")
    # ... execution logic
    return receipt

def withdraw_funds(account: Account, amount: Uint256) -> None:
    if account.balance < amount:
        raise InsufficientFunds(f"Balance {account.balance} < {amount}")
    # ... withdrawal logic
```

**Avoid:**
```python
def execute_transaction(tx: Transaction) -> Optional[Receipt]:
    if tx.gas_limit < INTRINSIC_GAS:
        return None  # Don't use None for errors
    # ... execution logic
    return receipt
```

## Runtime Checks

- Use `ensure(...)` for runtime condition validation
- Use `assert` **only** for:
  - Invariants and type assumptions  
  - Bug detection and debugging
  - **Never** for control flow or user-facing validation

**Good:**
```python
def transfer(sender: Account, recipient: Account, amount: Uint256) -> None:
    ensure(sender.balance >= amount, "Insufficient balance")  # Runtime validation
    ensure(amount > 0, "Transfer amount must be positive")    # Runtime validation
    
    # Internal invariant checks
    assert isinstance(sender.balance, Uint256)  # Type assumption
    assert sender.address != recipient.address  # Invariant check
```

**Avoid:**
```python
def transfer(sender: Account, recipient: Account, amount: Uint256) -> None:
    assert sender.balance >= amount  # Don't use assert for user validation
    assert amount > 0               # Don't use assert for control flow
```

## Type Annotations and Ignores

- **Never** use blanket `# type: ignore` comments
- If type ignoring is absolutely necessary:
  - Include the specific error code: `# type: ignore[error-code]`
  - Add a brief one-line comment explaining why

**Good:**
```python
# Specific error code with explanation
result = unsafe_cast(data)  # type: ignore[attr-defined]  # Legacy API compatibility

# Type checker limitation workaround  
value = getattr(obj, name, default)  # type: ignore[misc]  # Dynamic attribute access
```

**Avoid:**
```python
result = some_function()  # type: ignore  # Too broad, no explanation
data = process(input)     # type: ignore  # No error code specified
```

## Enforcement

These style rules are enforced through:

- **mypy** with strict configuration for type checking and ignore validation
- **Ruff** linting rules (including PGH003 for blanket type ignore detection)
- Code review processes

The CI pipeline will reject code that violates these guidelines.