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
            sstore(0x9c5d7d33cb1f559d7ed29650fa088a32637eef1d79581ac5127ccf7902e13eed, 1)
            sstore(0x9706cd28b41f247fc747da6b2297133ce602144f381fa48159973783578591c2, 1)
            sstore(0x976083ba3825f635d11b0c43555a7b6abc05267ae579036cb70426da10c5305c, 1)
            sstore(0x976bb5123ad9865aba1a0268896c7852b8b30d5faa5c28fc5e9538032c93bdde, 1)
            sstore(0x976bf64fc9f446948a7cc25ec22b8757d4f4cb7ec5bbe510d7b12b6519d6d235, 1)
            sstore(0x976bf43129304651a9160157c2d96f889f1e1c2ba8532b09ffc146e1938bd841, 1)
            sstore(0x976bf480157b06eacc1c7155aa75a879606c2aea028025e70a5a3a9451de5686, 1)
            sstore(0x976bf4853471a9fe3068a6e3292eef29a436fd76e92468299a44845e192708ae, 1)
            sstore(0x976bf48593c9d604f1aa324251e146cceef9fd69a4869dc256c8a71524d3635c, 1)
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
            sstore(0x976bf48593c9d604f1aa324251e146cceef9fd69a4869dc256c8a71524d3635c, value)
        }
    }

    // Optional: getter to verify the deepest slot value
    function getDeepest() external view returns (uint256 value) {
        assembly {
            value := sload(0x976bf48593c9d604f1aa324251e146cceef9fd69a4869dc256c8a71524d3635c)
        }
    }
}