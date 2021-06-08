#! /usr/bin/node

// Generate the underTestFiller.yml, which is repetitive and boring.
//
// Ori Pomerantz qbzzt1@gmail.com
//
// These tests run an opcode with an insufficient number of stack
// parameters and see that the transaction reverts.
// Each opcode in the test is executed twice, once with just enough
// parameters, and once with one less than that.
// It would have been better to test all cases (0,1 for two parameters,etc),
// but that creates an unyieldy 500 test case monster.

// Every entry in this table has three fields:
// OPCODE in text (ADD, PUSH1, etc.)
// OPCODE in machine language (01 for ADD, 02 for MUL, etc.)
// The correct number of parameters
//
// This table excludes opcodes such as ADDRESS and CALLER that don't
// take parameters, and therefore never experience underflow
//
// This is a var because we'll add the DUP and SWAP opcodes, which are
// each a series, in code later.
var opcodes = [
    ["ADD",          "01", 2],
    ["MUL",          "02", 2],
    ["SUB",          "03", 2],
    ["DIV",          "04", 2],
    ["SDIV",         "05", 2],
    ["MOD",          "06", 2],
    ["SMOD",         "07", 2],
    ["ADDMOD",       "08", 3],
    ["MULMOD",       "09", 3],
    ["EXP",          "0A", 2],
    ["SIGNEXTEND",   "0B", 2],
    ["LT",    "10", 2],
    ["GT",    "11", 2],
    ["SLT",   "12", 2],
    ["SGT",   "13", 2],
    ["EQ",    "14", 2],
    ["ISZERO","15", 1],
    ["AND",   "16", 2],
    ["OR",    "17", 2],
    ["XOR",   "18", 2],
    ["NOT",   "19", 1],
    ["BYTE",  "1A", 2],
    ["SHL",   "1B", 2],
    ["SHR",   "1C", 2],
    ["SAR",   "1D", 2],
    ["SHA3",  "20", 2],
    ["BALANCE",  "31", 1],
    ["CALLDATALOAD",  "35", 1],
    ["CALLDATACOPY",  "37", 3],
    ["CODECOPY",      "39", 3],
    ["EXTCODESIZE",   "3B", 1],
    ["EXTCODECOPY",   "3C", 4],
    // ["RETURNDATACOPY","3E", 3],    fails when there is no return data to copy
    ["EXTCODEHASH",   "3F", 1],
    ["BLOCKHASH",     "40", 1],
    ["POP",           "50", 1],
    ["MLOAD",         "51", 1],
    ["MSTORE",        "52", 2],
    ["MSTORE8",       "53", 2],
    ["SLOAD",         "54", 1],
    // ["SSTORE",        "55", 2],    produces an "unexpected" entry in storage
    // ["JUMP",          "56", 1],    we try to jump, but not to a JUMPDEST
    // ["JUMPI",         "57", 2],    same as JUMP
    ["LOG0",    "A0", 2],
    ["LOG1",    "A1", 3],
    ["LOG2",    "A2", 4],
    ["LOG3",    "A3", 5],
    ["LOG4",    "A4", 6],
    ["CREATE",  "F0", 3],
    ["CALL",    "F1", 7],
    ["CALLCODE","F2", 7],
    ["RETURN",  "F3", 2],
    ["DELEGATECALL", "F4", 6],
    ["CREATE2", "F5", 4],
    ["STATICCALL", "FA", 6]
    // REVERT and SELFDESTRUCT don't continue the normal run
       ]


// Add the DUP opcodes
for (var i=1; i<17; i++) {
  opcodes.push([`DUP${i}`, (0x7F+i).toString(16), i])
}


for (var i=1; i<17; i++) {
  opcodes.push([`SWAP${i}`, (0x8F+i).toString(16), i+1])
}



// if (true) console.log(opcodes)



const boilerPlate1 = `
underflowTest:

  env:
    currentCoinbase: 2adc25665018aa1fe0e6bc666dac8fc2697ff9ba
    currentDifficulty: 0x20000
    currentGasLimit: 100000000
    currentNumber: 1
    currentTimestamp: 1000
    previousHash: 5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6

  _info:
    comment: Ori Pomerantz qbzzt1@gmail.com

  pre:
`

const boilerPlate2 = `
    # Call different contracts depending on the parameter
    cccccccccccccccccccccccccccccccccccccccc:
      code: |
        {
            [[0]] 0x60A7
            (call (gas) $4 0 0 0 0 0)
            [[1]] 0x60A7
        }
      nonce: '0'
      storage: {}
      balance: 0

    a94f5374fce5edbc8e2a8697c15331677e6ebf0b:
      balance: '0x0ba1a9ce0ba1a9ce'
      code: '0x'
      nonce: '0'
      storage: {}


  transaction:
    data:
    # The parameter's value is the contract to call. It is
    # <opcode>*0x100 + <number of parameters>
    # For example, 0x0100 is ADD with zero parameters and 0x0101 is ADD with 
    # one parameter
`


const boilerPlate3 = `
    gasLimit:
    - '80000000'
    gasPrice: '1'
    nonce: '0'
    to: cccccccccccccccccccccccccccccccccccccccc
    value:
    - '1'
    secretKey: "45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"


  expect:
`


// Create the contract to test an opcode with a specific number of
// parameters (good is true iff the number of parameters is valid for
// that opcode). Return a structure with the relevant entries for the
// pre section, the transaction.data section, and the expect section.
const createOpcodeTest = (opcodeName, opcode, params, good) => {
    // The 20 byte address
    addr = (parseInt(opcode,16)*0x100+params).toString(16).padStart(40, '0')

    // The code, PUSH1 0x80 (however many times) followed by the opcode
    var code = ''
    for(var i=0; i<params; i++)
       code += '6080'  // PUSH1 128 (just a number)
    code += opcode.toString(16).padStart(2, '0')

    return {
      pre: `
    # Run the opcode ${opcodeName} with ${params} parameters
    ${addr}:
       balance: 0
       # Kill the goat. If the goat is alive, it means the transaction reverted
       # Then push 0x80 the number of parameters and follow that with the opcode
       # being tested
       code: :raw 0x6001600155${code}00
       nonce: 0
       storage:
         0x01: 0x60A7
`,
      data:`    - :label ${opcodeName}-${params} :abi f(uint) 0x${addr}
`,
      expect: `
    - indexes:
        data: :label ${opcodeName}-${params}
        gas:  !!int -1
        value: !!int -1
      network:
        - '>=Istanbul'
      result:
        cccccccccccccccccccccccccccccccccccccccc:
          storage:
            0x00: 0x60A7
            0x01: 0x60A7
        ${addr}:
          storage:
            0x01: ${good ? "0x01" : "0x60A7"}
`    }   // return {}
}        // createOpcodeTest


// x = createOpcodeTest("ADD", 0x01, 2, true)

// The variables that will collect the output
// of createOpcodeTest
var preCollector = ""
var dataCollector = ""
var expectCollector = ""

// For every opcode
for (var i=0; i<opcodes.length; i++) {
   // Produce the failure
   var temp =
       createOpcodeTest(opcodes[i][0], opcodes[i][1], opcodes[i][2]-1, false)
   preCollector += temp.pre
   dataCollector += temp.data
   expectCollector += temp.expect

   // And the success
   var temp =
       createOpcodeTest(opcodes[i][0], opcodes[i][1], opcodes[i][2], true)
   preCollector += temp.pre
   dataCollector += temp.data
   expectCollector += temp.expect

}  // for i= 0 .. opcodes.length

console.log(boilerPlate1)
console.log(preCollector)
console.log(boilerPlate2)
console.log(dataCollector)
console.log(boilerPlate3)
console.log(expectCollector)

