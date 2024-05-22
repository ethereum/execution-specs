# EOF Testing Coverage Tracker

- [ ] Example Test Case 1
- [x] Example Test Case 2 (./eip3540_eof_v1/test_example_valid_invalid.py::test_example_valid_invalid)
- [ ] Example Test Case 3 (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml)

## EIP-3540: EOF - EVM Object Format v1

### Validation

- [ ] Valid container without data section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Valid container with data section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Valid container with truncated data section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Valid container with data section truncated to empty (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Valid containers with multiple code sections (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml)
- [ ] Valid containers with max number of code sections
- [ ] Truncated magic (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Valid container except magic (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated before version  (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Valid container except version (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated before type section header (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated before type section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated type section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated before code section header (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml)
- [ ] Truncated before code section number (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated code section number (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated before code section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated code section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] 0 code section number (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml)
- [ ] 0 code section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] 0 code section size with non-empty data section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] No container sections, truncated before data section header (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Container sections present, truncated before data section header (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml)
- [ ] Truncated before data section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated data section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated before header terminator (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated before type section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Type section truncated before outputs (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Type section truncated before max_stack_height (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Type section truncated max_stack_height (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated before code sections (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated code section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Data section empty, trailing bytes (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Data section non-empty, trailing bytes (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Wrong order of sections (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] No data section header (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml)
- [ ] Multiple data sections (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Unknown section id (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Type section size != 4 * code section number (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml)
- [ ] Code section with max max_stack_height (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] Code section with max_stack_height above limit (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] Valid code sections with inputs/outputs
- [ ] Valid code section with max inputs
- [ ] Valid code section with max outputs
- [ ] Code sections with invalid number of inputs/outputs (above limit)
- [ ] 0 section with inputs/outputs (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] Multiple type section headers
- [ ] Multiple code section headers
- [ ] Multiple data section headers
- [ ] Container without type section (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] Container without code sections (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Container without data section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Valid containers without data section and with subcontainers
- [ ] Valid containers with data section and with subcontainers
- [ ] Valid container with maximum number of subcontainers
- [ ] Container with number of subcontainers above the limit
- [ ] Subcontainer section header truncated before subcontainer number
- [ ] Subcontainer section header truncated before subcontainer size
- [ ] Truncated subcontainer size
- [ ] 0 container section numner
- [ ] 0 container size
- [ ] Truncated container section body
- [ ] Multiple container section headers
- [ ] Invalid subcontainer
- [ ] Invalid subcontainer on a deep nesting level

## EIP-3670: EOF - Code Validation

### Validation

- [ ] Code section with invalid opcodes (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] INVALID opcode is valid (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] Truncated PUSH data (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)

## EIP-4200: EOF - Static relative jumps

### Validation

- [ ] Jumps out of section bounds (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)

## EIP-4750: EOF - Functions

### Validation

- [ ] Valid CALLFs  (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] CALLFs to non-existing sections  (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)

## EIP-5450: EOF - Stack Validation

### Validation

- [ ] Check all terminating opcodes (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] Code section not terminating (executing beyond section end) (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] Stack underflows (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] CALLF stack underflows (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] RETF with extra items on stack (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] Wrong max_stack_height (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)


## EIP-6206: EOF - JUMPF and non-returning functions

### Validation

- [ ] 0 section returning (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)

## EIP-7480: EOF - Data section access instructions

## EIP-663: SWAPN, DUPN and EXCHANGE instructions

## EIP-7069: Revamped CALL instructions

## EIP-7620: EOF Contract Creation

## EIP-7698: EOF - Creation transaction
