#!/usr/bin/env python
"""
Production-ready test suite for fuzzer bridge with geth verification.

This script:
1. Loads fuzzer output
2. Converts to blockchain test
3. Generates fixtures
4. Verifies with go-ethereum
5. Reports comprehensive results
"""

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ethereum_clis import GethTransitionTool
from ethereum_test_fixtures.blockchain import BlockchainFixture
from ethereum_test_specs.blockchain import BlockchainTest
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Block,
    Environment,
    Transaction,
)


class FuzzerBridge:
    """Production-ready fuzzer bridge with validation and verification."""

    def __init__(
        self,
        t8n_path: Optional[str] = None,
        verbose: bool = False,
        keep_fixtures: bool = False,
    ):
        """Initialize bridge with optional transition tool path."""
        self.t8n = GethTransitionTool(
            binary=Path(t8n_path) if t8n_path else None
        )
        self.verbose = verbose
        self.keep_fixtures = keep_fixtures
        self.stats: Dict[str, Any] = {
            "tests_generated": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "validation_errors": [],
        }

    def validate_fuzzer_output(self, data: Dict[str, Any]) -> List[str]:
        """Validate fuzzer output format and return list of errors."""
        errors = []

        # Check version
        version = data.get("version", "1.0")
        if version != "2.0":
            errors.append(f"Unsupported version {version}, expected 2.0")

        # Check required fields
        required_fields = [
            "accounts",
            "transactions",
            "env",
            "fork",
            "chainId",
        ]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Validate accounts with transactions have private keys
        if "accounts" in data and "transactions" in data:
            senders = set()
            for tx in data["transactions"]:
                sender = tx.get("from") or tx.get("sender")
                if sender:
                    senders.add(sender)

            for sender in senders:
                if sender not in data["accounts"]:
                    errors.append(f"Sender {sender} not in accounts")
                elif "privateKey" not in data["accounts"][sender]:
                    errors.append(f"No private key for sender {sender}")
                else:
                    # Validate private key matches address
                    if not self._validate_key_address(
                        data["accounts"][sender]["privateKey"], sender
                    ):
                        errors.append(
                            f"Private key doesn't match address {sender}"
                        )

        return errors

    def _validate_key_address(
        self, private_key: str, expected_address: str
    ) -> bool:
        """Validate that private key generates expected address."""
        try:
            from ethereum_test_types import EOA

            eoa = EOA(key=private_key)
            # EOA class returns the address directly via str()
            return str(eoa).lower() == expected_address.lower()
        except Exception:
            return False

    def convert_to_test(self, fuzzer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert fuzzer output to test parameters."""
        # Validate first
        errors = self.validate_fuzzer_output(fuzzer_data)
        if errors:
            raise ValueError("Validation failed:\n" + "\n".join(errors))

        # Build pre-state
        pre_state = Alloc()
        private_keys = {}

        for addr_str, account_data in fuzzer_data["accounts"].items():
            addr = Address(addr_str)

            if "privateKey" in account_data:
                private_keys[addr_str] = account_data["privateKey"]

            pre_state[addr] = Account(
                balance=int(account_data.get("balance", "0x0"), 16),
                nonce=int(account_data.get("nonce", "0x0"), 16),
                code=account_data.get("code", ""),
                storage=account_data.get("storage", {}),
            )

        # Create genesis environment (block 0)
        env_data = fuzzer_data["env"]
        genesis_env = Environment(
            fee_recipient=Address(env_data.get("currentCoinbase")),
            difficulty=0,  # Post-merge
            gas_limit=int(env_data.get("currentGasLimit", "0x1000000"), 16),
            number=0,  # Genesis is block 0
            timestamp=int(env_data.get("currentTimestamp", "0x1000"), 16) - 12,
            base_fee_per_gas=int(env_data.get("currentBaseFee", "0x7"), 16),
        )

        # Block 1 environment overrides
        block1_env = {
            "timestamp": int(env_data.get("currentTimestamp", "0x1000"), 16),
            "fee_recipient": Address(env_data.get("currentCoinbase")),
        }

        # Create transactions
        txs = []
        for tx_data in fuzzer_data["transactions"]:
            sender_addr = tx_data.get("from") or tx_data.get("sender")
            secret_key = private_keys[sender_addr]

            txs.append(
                Transaction(
                    to=Address(tx_data["to"]) if tx_data.get("to") else None,
                    value=int(tx_data.get("value", "0x0"), 16),
                    gas_limit=int(tx_data.get("gas", "0x5208"), 16),
                    gas_price=int(tx_data.get("gasPrice", "0x1"), 16),
                    nonce=int(tx_data.get("nonce", "0x0"), 16),
                    data=bytes.fromhex(tx_data.get("data", "0x")[2:])
                    if tx_data.get("data", "0x") != "0x"
                    else b"",
                    secret_key=secret_key,
                )
            )

        # Create block
        block = Block(txs=txs, **block1_env)

        return {
            "genesis_environment": genesis_env,
            "pre": pre_state,
            "post": {},
            "blocks": [block],
            "chain_id": fuzzer_data.get("chainId", 1),
            "fork": fuzzer_data.get("fork", "Prague"),
        }

    def generate_fixture(self, test_params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate blockchain test fixture."""
        # Get fork
        from ethereum_test_forks import Cancun, Osaka, Prague, Shanghai

        fork_map = {
            "Osaka": Osaka,
            "Prague": Prague,
            "Shanghai": Shanghai,
            "Cancun": Cancun,
        }
        fork = fork_map.get(test_params["fork"], Prague)

        # Create test
        test = BlockchainTest(
            genesis_environment=test_params["genesis_environment"],
            pre=test_params["pre"],
            post=test_params["post"],
            blocks=test_params["blocks"],
            chain_id=test_params["chain_id"],
        )

        # Generate fixture
        fixture = test.generate(
            t8n=self.t8n,
            fork=fork,
            fixture_format=BlockchainFixture,
        )

        self.stats["tests_generated"] += 1

        return fixture.model_dump(exclude_none=True, by_alias=True)

    def verify_with_geth(
        self, fixture: Dict[str, Any], geth_path: str, test_name: str = "test"
    ) -> Dict[str, Any]:
        """Verify fixture with go-ethereum evm tool."""
        # Write fixture to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump({test_name: fixture}, f, indent=2)
            fixture_path = f.name

        try:
            # Run geth blocktest
            result = subprocess.run(
                [geth_path, "blocktest", fixture_path],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Parse output
            output = result.stdout + result.stderr

            # Check if test passed
            if result.returncode == 0 and '"pass": true' in output:
                self.stats["tests_passed"] += 1
                return {
                    "pass": True,
                    "output": output,
                    "fixture_path": fixture_path,
                }
            else:
                self.stats["tests_failed"] += 1
                # Extract error message
                error = "Unknown error"
                if '"error":' in output:
                    import re

                    match = re.search(r'"error":\s*"([^"]+)"', output)
                    if match:
                        error = match.group(1)

                return {
                    "pass": False,
                    "error": error,
                    "output": output,
                    "fixture_path": fixture_path,
                }

        except subprocess.TimeoutExpired:
            self.stats["tests_failed"] += 1
            return {
                "pass": False,
                "error": "Timeout",
                "fixture_path": fixture_path,
            }
        except Exception as e:
            self.stats["tests_failed"] += 1
            return {
                "pass": False,
                "error": str(e),
                "fixture_path": fixture_path,
            }
        finally:
            # Optionally clean up
            # Note: args is not defined here - should be passed as parameter
            pass

    def run_full_test(self, fuzzer_file: str, geth_path: str) -> bool:
        """Run full test pipeline from fuzzer output to geth verification."""
        print(f"🔧 Loading fuzzer output from {fuzzer_file}")
        with open(fuzzer_file) as f:
            fuzzer_data = json.load(f)

        print("📋 Fuzzer Output Summary:")
        print(f"   Version: {fuzzer_data.get('version', 'unknown')}")
        print(f"   Fork: {fuzzer_data.get('fork', 'unknown')}")
        print(f"   Accounts: {len(fuzzer_data.get('accounts', {}))}")
        print(f"   Transactions: {len(fuzzer_data.get('transactions', []))}")

        # Validate
        print("\n✓ Validating fuzzer output...")
        errors = self.validate_fuzzer_output(fuzzer_data)
        if errors:
            print("❌ Validation failed:")
            for error in errors:
                print(f"   - {error}")
            return False

        # Convert
        print("✓ Converting to test parameters...")
        try:
            test_params = self.convert_to_test(fuzzer_data)
        except Exception as e:
            print(f"❌ Conversion failed: {e}")
            return False

        # Generate fixture
        print("✓ Generating blockchain test fixture...")
        try:
            fixture = self.generate_fixture(test_params)
        except Exception as e:
            print(f"❌ Fixture generation failed: {e}")
            import traceback

            traceback.print_exc()
            return False

        # Extract test info
        genesis_hash = fixture.get("genesisBlockHeader", {}).get(
            "hash", "unknown"
        )
        pre_count = len(fixture.get("pre", {}))
        print(f"   Genesis hash: {genesis_hash[:16]}...")
        print(f"   Pre-state accounts: {pre_count}")

        # Verify with geth
        print("\n🔍 Verifying with go-ethereum...")
        result = self.verify_with_geth(fixture, geth_path, "fuzzer_test")

        if result["pass"]:
            print("✅ Test PASSED!")
            if self.verbose:
                print(f"   Fixture: {result.get('fixture_path', 'N/A')}")
        else:
            print("❌ Test FAILED!")
            print(f"   Error: {result.get('error', 'Unknown')}")
            if self.verbose:
                print(f"   Output:\n{result.get('output', '')}")
            if self.keep_fixtures:
                print(f"   Fixture saved: {result.get('fixture_path', 'N/A')}")

        # Print statistics
        print("\n📊 Statistics:")
        print(f"   Tests generated: {self.stats['tests_generated']}")
        print(f"   Tests passed: {self.stats['tests_passed']}")
        print(f"   Tests failed: {self.stats['tests_failed']}")

        return result["pass"]


def main() -> int:
    """Main entry point for production test."""
    parser = argparse.ArgumentParser(
        description="Production test for fuzzer bridge with geth verification"
    )
    parser.add_argument(
        "--fuzzer-output",
        required=True,
        help="Path to fuzzer output JSON file",
    )
    parser.add_argument(
        "--geth-path", required=True, help="Path to go-ethereum evm binary"
    )
    parser.add_argument(
        "--t8n-path", help="Path to transition tool binary (optional)"
    )
    parser.add_argument(
        "--keep-fixtures",
        action="store_true",
        help="Keep generated fixture files for debugging",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Verbose output"
    )

    args = parser.parse_args()

    # Check paths exist
    if not Path(args.fuzzer_output).exists():
        print(f"❌ Fuzzer output not found: {args.fuzzer_output}")
        return 1

    if not Path(args.geth_path).exists():
        print(f"❌ Geth binary not found: {args.geth_path}")
        return 1

    # Run test
    bridge = FuzzerBridge(t8n_path=args.t8n_path)

    start_time = time.time()
    success = bridge.run_full_test(args.fuzzer_output, args.geth_path)
    elapsed = time.time() - start_time

    print(f"\n⏱️  Completed in {elapsed:.2f} seconds")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
