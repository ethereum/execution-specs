"""RPC helpers for priming and verifying fixture post-state assertions."""

from execution_testing.base_types import Hash
from execution_testing.fixtures import PostVerifications
from execution_testing.rpc import EthRPC

from .exceptions import LoggedError


def prime_post_verification_queries(
    eth_rpc: EthRPC,
    post_verifications: PostVerifications | None,
) -> None:
    """
    Read every state field that will later be verified through JSON-RPC.

    Priming the same RPC keys before block execution makes a client-side stale
    state cache observable after the chain advances: the final verification
    must return the post-state values rather than any value retained here.
    """
    if post_verifications is None:
        return

    for address, check in post_verifications.accounts.items():
        if check is None:
            # JSON-RPC cannot distinguish a nonexistent account from an empty
            # account directly. Prime every observable account-level field so
            # stale non-zero state can still be detected after execution.
            eth_rpc.get_balance(address)
            eth_rpc.get_transaction_count(address)
            eth_rpc.get_code(address)
            continue

        if check.balance is not None:
            eth_rpc.get_balance(address)
        if check.nonce is not None:
            eth_rpc.get_transaction_count(address)
        if check.code is not None:
            eth_rpc.get_code(address)
        if check.storage is not None:
            for key in check.storage:
                eth_rpc.get_storage_at(address, Hash(int(key)))


def verify_post_verification_queries(
    eth_rpc: EthRPC,
    post_verifications: PostVerifications | None,
) -> None:
    """Verify fill-time post-state assertions against the live client RPC."""
    if post_verifications is None:
        return

    for address, check in post_verifications.accounts.items():
        if check is None:
            balance = eth_rpc.get_balance(address)
            nonce = eth_rpc.get_transaction_count(address)
            code = eth_rpc.get_code(address)
            if balance != 0 or nonce != 0 or bytes(code) != b"":
                raise LoggedError(
                    f"Post-state RPC mismatch for {address}: expected "
                    "nonexistent/empty account, got "
                    f"balance={balance}, nonce={nonce}, "
                    f"code=0x{bytes(code).hex()}"
                )
            continue

        if check.balance is not None:
            got_balance = eth_rpc.get_balance(address)
            if got_balance != int(check.balance):
                raise LoggedError(
                    f"Post-state RPC balance mismatch for {address}: "
                    f"expected {int(check.balance)}, got {got_balance}"
                )

        if check.nonce is not None:
            got_nonce = eth_rpc.get_transaction_count(address)
            if got_nonce != int(check.nonce):
                raise LoggedError(
                    f"Post-state RPC nonce mismatch for {address}: "
                    f"expected {int(check.nonce)}, got {got_nonce}"
                )

        if check.code is not None:
            got_code = eth_rpc.get_code(address)
            if bytes(got_code) != bytes(check.code):
                raise LoggedError(
                    f"Post-state RPC code mismatch for {address}: "
                    f"expected 0x{bytes(check.code).hex()}, "
                    f"got 0x{bytes(got_code).hex()}"
                )

        if check.storage is not None:
            for key, expected_value in check.storage.items():
                got_value = eth_rpc.get_storage_at(address, Hash(int(key)))
                got_int = int.from_bytes(bytes(got_value), byteorder="big")
                if got_int != int(expected_value):
                    raise LoggedError(
                        f"Post-state RPC storage mismatch for {address} at "
                        f"slot {Hash(int(key))}: expected "
                        f"{int(expected_value)}, got {got_int}"
                    )
