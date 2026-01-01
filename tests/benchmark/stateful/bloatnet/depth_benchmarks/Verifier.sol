// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title Verifier
 * @dev Minimal contract to verify that an attacked contract's deep storage slot was updated.
 *      Called at the end of the attack execution to confirm the attack succeeded.
 */
contract Verifier {
    /**
     * @dev Verifies that the target contract's deepest storage slot contains the expected value.
     * @param target The address of the attacked contract
     * @param expectedValue The expected value in the deep storage slot
     * @return success True if the value matches, false otherwise
     */
    function verify(address target, uint256 expectedValue) external view returns (bool success) {
        // Call getDeepest() on target - selector is 0x77b5b7e6
        // bytes4(keccak256("getDeepest()")) = 0x77b5b7e6
        (bool callSuccess, bytes memory data) = target.staticcall(
            abi.encodeWithSelector(0x77b5b7e6)
        );

        if (!callSuccess || data.length != 32) {
            return false;
        }

        uint256 actualValue = abi.decode(data, (uint256));
        return actualValue == expectedValue;
    }
}
