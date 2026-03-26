#! /usr/bin/node

// Generate the vmArithmeticTest/twoOpsFiller.yml file
//
// Ori Pomerantz qbzzt1@gmail.com
//
// This test looks at the result of running two operations (numeric/bitwise)
// There are 24 such operations, so 576 test cases.


// Turn boolean values into the numbers the evm gives us
const bool2num = a => a ? 1n : 0n

// The EVM is 256 bits, and uses 2's complement for negatives.
// JavaScript BigInt, OTOH, can be a lot more (it seems to depend on the size of
// the biggest operand).
// In the few cases where the sign matters these functions convert between representations.

// The unsigned value is always the least significant 256 bits
const makeUnsigned = a => a & (2n**256n-1n)

// The signed value can be either positive (no change) or negative. If it's
// negative, the most significant bit is on. In that case, use 2's complement
// to figure the absolute value and then negate it.
const makeSigned =   a => (a & 2n**255n) ? -(makeUnsigned(~a)+1n) : a


// The numeric/bitwise opcodes we test. For each we have:
//
// name
// byte for the opcode (used for storage cells)
// number of parameters it receives
// Javascript function to implement it so we'll be able to know what result to expect

var opcodes = [
    ["ADD",         '01', 2, (a,b) => a+b],
    ["MUL",         '02', 2, (a,b) => a*b],
    ["SUB",         '03', 2, (a,b) => a-b],
    ["DIV",         '04', 2, (a,b) => a/b],
    ["SDIV",        '05', 2, (a,b) => makeUnsigned(makeSigned(a)/makeSigned(b))],
    ["MOD",         '06', 2, (a,b) => a % b],
    ["SMOD",        '07', 2, (a,b) => makeUnsigned(makeSigned(a) % makeSigned(b))],
    ["ADDMOD",      '08', 3, (a,b,c) => (a+b) % c],
    ["MULMOD",      '09', 3, (a,b,c) => (a*b) % c],
    ["EXP",         '0a', 2, (a,b) => a**b],
    ["LT",          '10', 2, (a,b) => bool2num(a<b)],
    ["GT",          '11', 2, (a,b) => bool2num(a>b)],
    ["SLT",         '12', 2, (a,b) => bool2num(makeSigned(a)<makeSigned(b))],
    ["SGT",         '13', 2, (a,b) => bool2num(makeSigned(a)>makeSigned(b))],
    ["EQ",          '14', 2, (a,b) => bool2num(a==b)],
    ["ISZERO",      '15', 1, a => bool2num(a == 0)],
    ["AND",         '16', 2, (a,b) => a&b],
    ["OR",          '17', 2, (a,b) => a|b],
    ["XOR",         '18', 2, (a,b) => a^b],
    ["NOT",         '19', 1, a => makeUnsigned(~a)],
    ["BYTE",        '1a', 2, (i,x) => i > 32 ? 0 : (x >> (248n - i*8n)) & 255n],
    ["SHL",         '1b', 2, (a,b) => (a > 255n) ? 0 : b << a],
    ["SHR",         '1c', 2, (a,b) => b >> a],
    ["SAR",         '1d', 2, (a,b) => b >> a],
       ]



// Turn an opcode line into LLL code with these values. a,b,c are code structures
// Code structures contain two fields:
// lll - the LLL code for the operation
// val - the numeric result (as a BigInt)
const opcode2Code = (op, a, b, c) => {

  // The result depends on the number of parameters the opcode accepts
  switch(op[2]) {
    case 1:
      return { lll: `(${op[0]} ${a.lll})`, val: op[3](a.val) }
      break;
    case 2:
      return { lll: `(${op[0]} ${a.lll} ${b.lll})`, val: op[3](a.val,b.val) }
      break;
    case 3:
      return { lll: `(${op[0]} ${a.lll} ${b.lll} ${c.lll})`, val: op[3](a.val,b.val,c.val) }
      break;
  }    // switch(op[1])
}   // opcode2Code


// The values we use as operands
one = {lll: "1", val: BigInt(1)}
two = {lll: "2", val: BigInt(2)}
three = {lll: "3", val: BigInt(3)}


const boilerPlate1 = `
twoOps:
  # Generated automatically by twoOpsGen.js

  env:
    currentCoinbase: 2adc25665018aa1fe0e6bc666dac8fc2697ff9ba
    currentDifficulty: 0x20000
    currentGasLimit: 100000000
    currentNumber: 1
    currentTimestamp: 1000

  _info:
    comment: Ori Pomerantz qbzzt1@gmail.com

  pre:
    a94f5374fce5edbc8e2a8697c15331677e6ebf0b:
      balance: '0x0ba1a9ce0ba1a9ce'
      code: '0x'
      nonce: '0'
      storage: {}

    # Calculate the results
    cccccccccccccccccccccccccccccccccccccccc:
      code: |
        {
`

const boilerPlate2 = `
        }
      nonce: 1
      storage: {}
      balance: 0



  transaction:
    data: 
    - :raw 0x00
    gasLimit:
    - '80000000'
    gasPrice: '1'
    nonce: '0'
    to: cccccccccccccccccccccccccccccccccccccccc
    value:
    - '1'
    secretKey: "45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"


  expect:
   - indexes:
        data: !!int -1
        gas:  !!int -1
        value: !!int -1
     network:
        - '>=Istanbul'
     result:
        cccccccccccccccccccccccccccccccccccccccc:
          storage:`


// Create the lines to test a specific combo
const createOpcodeTest = (op1, op2) => {
    // The storage cell for the result
    cell0 = `0x1100${op1[1]}00${op2[1]}0000`
    cell1 = `0x1100${op1[1]}00${op2[1]}0001`


    intermediate = opcode2Code(op2, two, one, three)
    code0 = opcode2Code(op1, intermediate, three, two)
    code1 = opcode2Code(op1, intermediate, one, two)


    // This structure contains these fields:
    // lll - the line to place into the cc..cc contract LLL
    // res - the result to place into the expect section
    return {
      lll: `
            [[${cell0}]] ${code0.lll}
            [[${cell1}]] ${code1.lll}`,
      res: `
            ${cell0}: ${makeUnsigned(BigInt(code0.val))}
            ${cell1}: ${makeUnsigned(BigInt(code1.val))}`
    }   // return {}

}        // createOpcodeTest


// The variables that will collect the output
// of createOpcodeTest
var lllCollector = ""
var resCollector = ""


// For every opcode pair we can get from the list
for (var op1Num=0; op1Num<opcodes.length; op1Num++)
    for (var op2Num=0; op2Num<opcodes.length; op2Num++) {
      temp = createOpcodeTest(opcodes[op1Num], opcodes[op2Num])
      lllCollector += temp.lll
      resCollector += temp.res
    }    // for every opcode pair



console.log(boilerPlate1)
console.log(lllCollector)
console.log(boilerPlate2)
console.log(resCollector)
