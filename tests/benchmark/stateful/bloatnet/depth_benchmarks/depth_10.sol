// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract WorstCaseERC20 {
    // ERC20 State
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    uint256 public totalSupply;

    // Token metadata - returning constants to save gas
    string public constant name = "WorstCase";
    string public constant symbol = "WORST";
    uint8 public constant decimals = 18;

    constructor() {
        // Mint total supply to deployer
        totalSupply = 1_000_000_000 * 10 ** 18; // 1 billion tokens
        balanceOf[msg.sender] = totalSupply;

        // Set all mined storage slots to 1
        assembly {
            sstore(0xfeb1bc66963690bd7d902e86ccaf4e0fa1ea72277653d012a3fed288892770fc, 1)
            sstore(0xf7df78bf2009da798ad808c14e99d4b0b1351493558cf3172d4c9ab38edcdad2, 1)
            sstore(0xf71150ce002de523152da00b34a46728867ac39c68cfede6e5e6be804e36ad33, 1)
            sstore(0xf71b286886de2caf0f4e66d925abafa1ecff0218dde77b91a0b103b3a969df72, 1)
            sstore(0xf71b24d7942831944a4a6c9a9a650b26162af41802b57c6a349480b3139ec9c0, 1)
            sstore(0xf71b2efa932b6b0e7fdaa9e725d8fff777744cbb015ade8e56b791ba7024e812, 1)
            sstore(0xf71b2e5b7127047a0ea71e879c8a7fbf3aa423ab284ff119e2e7874bf34264a5, 1)
            sstore(0xf71b2e583d6ed22307e56f66f0d15664401d31de25500eb08b2b6bc507a5f947, 1)
            sstore(0xf71b2e583a4893d4003d080cb2c6524d4461283bd7a198ae5d17b877cb58188b, 1)
            sstore(0xf71b2e583db6708d2eb5ed9f0aab56cbe346a1efcaf18c5eec5a177120a2d119, 1)
        }
    }

    // Minimal ERC20 implementation
    function transfer(address to, uint256 amount) public returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        return true;
    }

    function approve(address spender, uint256 amount) public returns (bool) {
        allowance[msg.sender][spender] = amount;
        return true;
    }

    function transferFrom(
        address from,
        address to,
        uint256 amount
    ) public returns (bool) {
        require(balanceOf[from] >= amount, "Insufficient balance");
        require(
            allowance[from][msg.sender] >= amount,
            "Insufficient allowance"
        );

        balanceOf[from] -= amount;
        balanceOf[to] += amount;
        allowance[from][msg.sender] -= amount;

        return true;
    }

    // Attack method - writes to the deepest storage slot
    function attack(uint256 value) external {
        assembly {
            sstore(0xf71b2e583db6708d2eb5ed9f0aab56cbe346a1efcaf18c5eec5a177120a2d119, value)
        }
    }

    // Optional: getter to verify the deepest slot value
    function getDeepest() external view returns (uint256 value) {
        assembly {
            value := sload(0xf71b2e583db6708d2eb5ed9f0aab56cbe346a1efcaf18c5eec5a177120a2d119)
        }
    }
}