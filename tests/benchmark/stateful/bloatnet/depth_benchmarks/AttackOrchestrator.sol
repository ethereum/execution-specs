// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title AttackOrchestrator
 * @dev Orchestrates attacks on CREATE2-deployed contracts by deriving their addresses
 *      and calling attack(uint256) on each one within a specified range.
 */
contract AttackOrchestrator {
    // Immutable storage for gas efficiency
    address public immutable deployerAddress;
    bytes32 public immutable initCodeHash;

    // Attack function selector for attack(uint256)
    bytes4 private constant ATTACK_SELECTOR = 0x64dd891a;

    /**
     * @dev Constructor sets the deployer address and init code hash
     * @param _deployer The address that deployed the target contracts via CREATE2
     * @param _initCodeHash The keccak256 hash of the target contract's init code
     */
    constructor(address _deployer, bytes32 _initCodeHash) {
        deployerAddress = _deployer;
        initCodeHash = _initCodeHash;
    }

    /**
     * @dev Executes attacks on a range of CREATE2-deployed contracts
     * @param value The value to pass to each attack() call
     * @param startIndex The starting index (inclusive)
     * @param endIndex The ending index (exclusive)
     */
    function attack(uint256 value, uint256 startIndex, uint256 endIndex) external {
        // Load immutables into local variables for assembly access
        address _deployer = deployerAddress;
        bytes32 _codeHash = initCodeHash;

        // Use assembly for gas-efficient CREATE2 address derivation and calls
        assembly {
            // Use local variables instead of immutables
            let deployer := _deployer
            let codeHash := _codeHash

            // Loop through the range
            for { let i := startIndex } lt(i, endIndex) { i := add(i, 1) } {
                // Derive CREATE2 address
                // Formula: keccak256(0xff ++ deployer ++ salt ++ initCodeHash)[12:]

                // Store CREATE2 preimage in memory
                // The layout should be: 0xff (1 byte) + deployer (20 bytes) + salt (32 bytes) + codeHash (32 bytes)
                // Total: 85 bytes
                let memPtr := 0x00
                mstore8(memPtr, 0xff)                                    // 0xff prefix at byte 0
                mstore(add(memPtr, 0x01), shl(96, deployer))            // deployer address at bytes 1-20
                mstore(add(memPtr, 0x15), i)                            // salt (i as uint256) at bytes 21-52
                mstore(add(memPtr, 0x35), codeHash)                     // init code hash at bytes 53-84

                // Compute CREATE2 address
                let target := and(
                    keccak256(0x00, 0x55),            // Hash 85 bytes
                    0xffffffffffffffffffffffffffffffffffffffff  // Mask to 20 bytes
                )

                // Prepare memory for the attack call at a different location to avoid overwriting
                let callDataPtr := 0x80
                // Hardcode the selector directly: 0x64dd891a shifted left by 224 bits
                mstore(callDataPtr, 0x64dd891a00000000000000000000000000000000000000000000000000000000)
                mstore(add(callDataPtr, 0x04), value)           // Value parameter

                // Call attack(value) with 3,650 gas (optimal for SSTORE to deep slot)
                // Breakdown: 2,900 gas for cold SSTORE + 342 gas for function overhead + 400 gas safety margin
                let success := call(
                    3650,       // gas
                    target,     // to
                    0,          // value (0 ETH)
                    callDataPtr,// argsOffset (where we stored the call data)
                    0x24,       // argsSize (4 + 32 = 36 bytes)
                    0,          // retOffset (don't store return data)
                    0           // retSize
                )

                // Continue regardless of success
                // No need to check success, just continue to next iteration
            }
        }
    }

    /**
     * @dev Fallback function to execute attacks when called directly
     *      This allows the contract to execute in its constructor if needed
     */
    fallback() external {
        // Could implement constructor-based attack here if needed
    }
}