# EOF Testing Coverage Tracker

- [ ] Example Test Case 1
- [x] Example Test Case 2 (./eip3540_eof_v1/test_example_valid_invalid.py::test_example_valid_invalid)
- [ ] Example Test Case 3 (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml)

## EIP-3540: EOF - EVM Object Format v1

### Validation

- [ ] Empty code is not a valid EOF (ethereum/tests: src/EOFTestsFiller/efValidation/validate_empty_code_Copier.json)
- [ ] Valid container without data section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/minimal_valid_EOF1_code_Copier.json)
- [ ] Valid container with data section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/minimal_valid_EOF1_code_with_data_Copier.json)
- [ ] Valid container with truncated data section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_truncated_section_Copier.json)
- [ ] Valid container with data section truncated to empty (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Valid containers with multiple code sections (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml src/EOFTestsFiller/efValidation/minimal_valid_EOF1_multiple_code_sections_Copier.json)
- [ ] Valid containers with max number of code sections (ethereum/tests: src/EOFTestsFiller/efValidation/many_code_sections_1024_Copier.json src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [ ] Too many code sections (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_too_many_code_sections_Copier.json src/EOFTestsFiller/efValidation/too_many_code_sections_Copier.json)
- [ ] Truncated magic (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [x] Valid container except magic (./eip3540_eof_v1/test_container_validation.py::test_magic_validation ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/validate_EOF_prefix_Copier.json)
- [ ] Truncated before version  (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [x] Valid container except version (./eip3540_eof_v1/test_container_validation.py::test_version_validation ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/validate_EOF_version_Copier.json)
- [ ] Truncated before type section header (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated before type section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_incomplete_section_size_Copier.json)
- [ ] Truncated type section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_incomplete_section_size_Copier.json)
- [ ] No type section header (ethereum/tests: src/EOFTestsFiller/efValidation/EOF1_no_type_section_Copier.json)
- [ ] Truncated before code section header (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml)
- [ ] Truncated before code section number (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml )
- [ ] Truncated code section number (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_incomplete_section_size_Copier.json)
- [ ] Truncated before code section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated code section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_incomplete_section_size_Copier.json)
- [ ] No code section header (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_code_section_missing_Copier.json) 
- [ ] 0 code section number (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml)
- [ ] 0 code section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml ./src/EOFTestsFiller/efValidation/EOF1_code_section_0_size_Copier.json)
- [ ] 0 code section size with non-empty data section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] No container sections, truncated before data section header (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Container sections present, truncated before data section header (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml)
- [ ] Truncated before data section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_incomplete_section_size_Copier.json)
- [ ] Truncated data section size (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_incomplete_section_size_Copier.json)
- [x] Truncated before header terminator (ethereum/tests: src/EOFTestsFiller/efValidation/EOF1_header_not_terminated_Copier.json)
- [ ] Truncated before header terminator (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated before type section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_truncated_section_Copier.json)
- [ ] Type section truncated before outputs (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Type section truncated before max_stack_height (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Type section truncated max_stack_height (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_truncated_section_Copier.json)
- [ ] Truncated before code sections (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Truncated code section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_truncated_section_Copier.json)
- [ ] Data section empty, trailing bytes (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_trailing_bytes_Copier.json)
- [ ] Data section non-empty, trailing bytes (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_trailing_bytes_Copier.json)
- [ ] Wrong order of sections (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_section_order_Copier.json ./src/EOFTestsFiller/efValidation/EOF1_data_section_before_code_section_Copier.json ./src/EOFTestsFiller/efValidation/EOF1_data_section_before_types_section_Copier.json src/EOFTestsFiller/efValidation/EOF1_type_section_not_first_Copier.json)
- [ ] No data section header (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml src/EOFTestsFiller/efValidation/data_section_missing_Copier.json)
- [ ] Multiple data sections (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Unknown section id (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_unknown_section_Copier.json)
- [ ] Type section size != 4 * code section number (ethereum/tests: ./src/EOFTestsFiller/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_invalid_type_section_size_Copier.json src/EOFTestsFiller/efValidation/EOF1_types_section_0_size_Copier.json)
- [ ] Code section with max max_stack_height (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] Code section with max_stack_height above limit (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/efValidation/max_stack_height_Copier.json)
- [ ] Valid code sections with inputs/outputs (ethereum/tests: ./src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [ ] Valid code section with max inputs
- [ ] Valid code section with max outputs
- [ ] Code sections with invalid number of inputs/outputs (above limit)
- [ ] 0 section with inputs/outputs (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_invalid_section_0_type_Copier.json src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [ ] Multiple type section headers (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_multiple_type_sections_Copier.json)
- [ ] Multiple code section headers (ethereum/tests: src/EOFTestsFiller/efValidation/multiple_code_sections_headers_Copier.json)
- [ ] Multiple data section headers (ethereum/tests: src/EOFTestsFiller/efValidation/EOF1_multiple_data_sections_Copier.json)
- [ ] Container without type section (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_type_section_missing_Copier.json src/EOFTestsFiller/efValidation/EOF1_types_section_missing_Copier.json)
- [ ] Container without code sections (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Container without data section (ethereum/tests: ./src/EOFTestsFiller/EIP3540/validInvalidFiller.yml)
- [ ] Valid containers without data section and with subcontainers (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_embedded_container_Copier.json)
- [ ] Valid containers with data section and with subcontainers (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_embedded_container_Copier.json)
- [ ] Valid container with maximum number of subcontainers (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_embedded_container_Copier.json)
- [ ] Container with number of subcontainers above the limit (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_embedded_container_invalid_Copier.json)
- [ ] Subcontainer section header truncated before subcontainer number (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_embedded_container_invalid_Copier.json)
- [ ] Subcontainer section header truncated before subcontainer size (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_embedded_container_invalid_Copier.json)
- [ ] Truncated subcontainer size (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_embedded_container_invalid_Copier.json)
- [ ] 0 container section number (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_embedded_container_invalid_Copier.json)
- [ ] 0 container size (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_embedded_container_invalid_Copier.json)
- [ ] Truncated container section body (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_embedded_container_invalid_Copier.json)
- [ ] Multiple container section headers
- [ ] Invalid subcontainer
- [ ] Invalid subcontainer on a deep nesting level
- [ ] Max number of inputs/outputs in a section (ethereum/tests: src/EOFTestsFiller/efValidation/max_arguments_count_Copier.json)
- [ ] Number of inputs/outputs in a section above the limit (ethereum/tests: src/EOFTestsFiller/efValidation/max_arguments_count_Copier.json)

### Execution

- [ ] Execution of EOF contracts (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_ExecutionFiller.yml)
- [ ] Legacy executing EXTCODESIZE of EOF contract (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_ExecutionFiller.yml)
- [ ] Legacy executing EXTCODEHASH of EOF contract (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_ExecutionFiller.yml)
- [ ] Legacy executing EXTCODECOPY of EOF contract (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_ExecutionFiller.yml)
- [ ] `*CALLs` from legacy contracts to EOF contracts (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_CallsFiller.yml)
- [ ] `EXT*CALLs` from EOF to legacy contracts (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_CallsFiller.yml)
- [ ] EXTDELEGATECALL from EOF to EOF contract (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_CallsFiller.yml)
- [ ] EXTDELEGATECALL from EOF to legacy contract failing (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_CallsFiller.yml)
- [ ] EXTDELEGATECALL from EOF to EOA failing
- [ ] EXTDELEGATECALL from EOF to empty account failing


## EIP-3670: EOF - Code Validation

### Validation

- [ ] Code section with invalid opcodes is rejected (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_undefined_opcodes_Copier.json src/EOFTestsFiller/EIP3670/validInvalidFiller.yml)
- [ ] INVALID opcode is valid (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] Truncated PUSH data (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/efValidation/EOF1_truncated_push_Copier.json src/EOFTestsFiller/EIP3670/validInvalidFiller.yml)
- [ ] Opcodes deprecated in EOF are rejected (ethereum/tests: src/EOFTestsFiller/efValidation/deprecated_instructions_Copier.json ethereum/tests: src/EOFTestsFiller/EIP3670/validInvalidFiller.yml)
- [ ] Codes with each valid opcodes (ethereum/tests: src/EOFTestsFiller/EIP3670/validInvalidFiller.yml)
- [ ] Undefined instruction after terminating instruction (ethereum/tests: src/EOFTestsFiller/EIP3670/validInvalidFiller.yml)

## EIP-4200: EOF - Static relative jumps

### Validation

- [ ] Valid RJUMP with various offsets (ethereum/tests: src/EOFTestsFiller/efValidation/EOF1_valid_rjump_Copier.json src/EOFTestsFiller/EIP4200/validInvalidFiller.yml)
- [ ] Valid RJUMP with maximum offset (ethereum/tests: src/EOFTestsFiller/EIP4200/validInvalidFiller.yml)
- [ ] Valid RJUMP with minimum offset
- [ ] Valid RJUMPI with various offsets (ethereum/tests: src/EOFTestsFiller/efValidation/EOF1_valid_rjumpi_Copier.json src/EOFTestsFiller/EIP4200/validInvalidFiller.yml)
- [ ] Valid RJUMPI with maximum offset (ethereum/offset: src/EOFTestsFiller/EIP4200/validInvalidFiller.yml)
- [ ] Valid RJUMPI with minimum offset
- [ ] Valid RJUMPV with various number of offsets and various offsets (ethereum/tests: src/EOFTestsFiller/efValidation/EOF1_valid_rjumpv_Copier.json src/EOFTestsFiller/EIP4200/validInvalidFiller.yml)
- [ ] Valid RJUMPV with table size 256 (ethereum/tests: src/EOFTestsFiller/EIP4200/validInvalidFiller.yml)
- [ ] Valid RJUMPV containing maximum offset (ethereum/tests: src/EOFTestsFiller/EIP4200/validInvalidFiller.yml)
- [ ] Valid RJUMPV containing minimum offset
- [ ] Truncated before RJUMP immediate (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjump_truncated_Copier.json)
- [ ] Truncated RJUMP immediate (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjump_truncated_Copier.json)
- [ ] RJUMP out of container bounds (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjump_invalid_destination_Copier.json)
- [ ] RJUMP out of section bounds (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjump_invalid_destination_Copier.json)
- [ ] RJUMP into immediate (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjump_invalid_destination_Copier.json)
- [ ] Truncated before RJUMPI immediate (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjumpi_truncated_Copier.json)
- [ ] Truncated RJUMPI immediate (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjumpi_truncated_Copier.json)
- [ ] RJUMPI out of container bounds (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjumpi_invalid_destination_Copier.json)
- [ ] RJUMPI out of section bounds (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjumpi_invalid_destination_Copier.json)
- [ ] RJUMPI into immediate (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjumpi_invalid_destination_Copier.json)
- [ ] Truncated before RJUMPV immediate
- [ ] Truncated RJUMPV immediate (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjumpv_truncated_Copier.json)
- [ ] RJUMPV out of container bounds (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjumpv_invalid_destination_Copier.json)
- [ ] RJUMPV out of section bounds (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjumpv_invalid_destination_Copier.json)
- [ ] RJUMPV into immediate (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_rjumpv_invalid_destination_Copier.json)

### Execution

- [x] RJUMP forwards (eip7692_eof_v1/eip4200_relative_jumps/test_rjump.py::test_rjump_positive_negative)
- [x] RJUMP backwards (eip7692_eof_v1/eip4200_relative_jumps/test_rjump.py::test_rjump_positive_negative)
- [x] RJUMP with 0 offset (eip7692_eof_v1/eip4200_relative_jumps/test_rjump.py::test_rjump_zero)
- [x] RJUMPI forwards with condition true/false (eip7692_eof_v1/eip4200_relative_jumps/test_rjumpi.py::test_rjumpi_condition_forwards)
- [x] RJUMPI backwards with condition true/false (eip7692_eof_v1/eip4200_relative_jumps/test_rjumpi.py::test_rjumpi_condition_backwards)
- [x] RJUMPI with 0 offset with condition true/false (eip7692_eof_v1/eip4200_relative_jumps/test_rjumpi.py::test_rjumpi_condition_zero)
- [x] RJUMPV with different case values (eip7692_eof_v1/eip4200_relative_jumps/test_rjumpv.py::test_rjumpv_condition)
- [x] RJUMPV with case value out of table bounds (eip7692_eof_v1/eip4200_relative_jumps/test_rjumpv.py::test_rjumpv_condition)
- [x] RJUMPV with max cases number (eip7692_eof_v1/eip4200_relative_jumps/test_rjumpv.py::test_rjumpv_condition eip7692_eof_v1/eip4200_relative_jumps/test_rjumpv.py::test_rjumpv_full_table*)

## EIP-4750: EOF - Functions

### Validation

- [ ] Valid CALLFs  (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml)
- [ ] CALLFs to non-existing sections  (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/efValidation/callf_invalid_code_section_index_Copier.json src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [ ] Truncated CALLF immediate (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_callf_truncated_Copier.json src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [ ] Unreachable code sections (ethereum/tests: src/EOFTestsFiller/efValidation/unreachable_code_sections_Copier.json)
- [ ] Sections reachable from other sections, but not reachable from section 0 (ethereum/tests: src/EOFTestsFiller/efValidation/unreachable_code_sections_Copier.json)
- [ ] RETF with maximum number of outputs (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)

### Execution

- [ ] CALLF/RETF execution (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP4200/CALLF_RETF_ExecutionFiller.yml)
- [ ] Dispatch to CALLF to different functions based on calldata (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP4200/CALLF_RETF_ExecutionFiller.yml)
- [ ] Maximum number of code sections, calling each section with CALLF (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP4200/CALLF_RETF_ExecutionFiller.yml)

## EIP-5450: EOF - Stack Validation

### Validation

#### Terminating instructions

- [ ] Check all terminating opcodes (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [ ] Code section not terminating (executing beyond section end) (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/EIP5450/validInvalidFiller.yml src/EOFTestsFiller/efStack/no_terminating_instruction_Copier.json)
- [ ] Code section ending with NOP (not terminating) (src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [ ] Check that unreachable code is invalid after all terminating instructions (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml src/EOFTestsFiller/efStack/unreachable_instructions_Copier.json)

#### Jumps

##### RJUMP

- [ ] Valid RJUMP backwards in a constant stack segment (ethereum/tests: src/EOFTestsFiller/efStack/backwards_rjump_Copier.json)
- [ ] Invalid RJUMP backwards with mismatching stack in a constant stack segment(ethereum/tests: src/EOFTestsFiller/efStack/backwards_rjump_Copier.json)
- [ ] Valid RJUMP backwards in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/backwards_rjump_variable_stack_Copier.json)
- [ ] Invalid RJUMP backwards with mismatching stack in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/backwards_rjump_variable_stack_Copier.json)
- [ ] Valid RJUMP forwards (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjump_Copier.json)
- [ ] Valid RJUMP forwards from different stack (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjump_Copier.json)
- [ ] Valid RJUMP forwards in variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjump_variable_stack_Copier.json)
- [ ] Valid RJUMP forwards from different stack in variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjump_variable_stack_Copier.json)
- [ ] Valid empty infinite loop with RJUMP (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [ ] Valid balanced infinite loop (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)

##### RJUMPI

- [ ] Valid RJUMPI backwards in a constant stack segment (ethereum/tests: src/EOFTestsFiller/efStack/backwards_rjumpi_Copier.json)
- [ ] Invalid RJUMPI backwards with mismatching stack in a constant stack segment(ethereum/tests: src/EOFTestsFiller/efStack/backwards_rjumpi_Copier.json)
- [ ] Valid RJUMPI backwards in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/backwards_rjumpi_variable_stack_Copier.json)
- [ ] Invalid RJUMPI backwards with mismatching stack in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/backwards_rjumpi_variable_stack_Copier.json)
- [ ] RJUMPI forward with branches of equal stack height (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_Copier.json src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [ ] RJUMPI forward with branches of equal stack height in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_variable_stack_Copier.json)
- [ ] RJUMPI forward with branches of different stack height (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_Copier.json src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [ ] RJUMPI forward with branches of different stack height in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_variable_stack_Copier.json)
- [ ] Valid loop using RJUMPI (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [ ] Valid loop with a break using RJUMPI - equal stack after break and normal loop end (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_Copier.json)
- [ ] Valid loop with a break using RJUMPI - equal stack after break and normal loop end, variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_variable_stack_Copier.json)
- [ ] Valid loop with a break using RJUMPI - different stack after break and normal loop end (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_Copier.json)
- [ ] Valid loop with a break using RJUMPI - different stack after break and normal loop end, variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_variable_stack_Copier.json)
- [ ] If-then-else with equal stack height in branches (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_Copier.json)
- [ ] If-then-else with equal stack height in branches, variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_variable_stack_Copier.json)
- [ ] If-then-else with different stack height in branches (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_Copier.json)
- [ ] If-then-else with different stack height in branches, variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_variable_stack_Copier.json)

##### RJUMPV

- [ ] Valid RJUMPV backwards in a constant stack segment (ethereum/tests: src/EOFTestsFiller/efStack/backwards_rjumpv_Copier.json)
- [ ] Invalid RJUMPV backwards with mismatching stack in a constant stack segment(ethereum/tests: src/EOFTestsFiller/efStack/backwards_rjumpv_Copier.json)
- [ ] Valid RJUMPV backwards in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/backwards_rjumpv_variable_stack_Copier.json)
- [ ] Invalid RJUMPV backwards with mismatching stack in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/backwards_rjumpv_variable_stack_Copier.json)
- [ ] RJUMPV forward with branches of equal stack height (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpv_Copier.json src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [ ] RJUMPV forward with branches of equal stack height in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpv_variable_stack_Copier.json)
- [ ] RJUMPV forward with branches of different stack height (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpv_Copier.json src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [ ] RJUMPV forward with branches of different stack height  in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpv_variable_stack_Copier.json)
- [ ] Valid infinite loop using RJUMPV (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [ ] Switch with equal stack height in branches (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpv_Copier.json)
- [ ] Switch with equal stack height in branches, variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpv_variable_stack_Copier.json)
- [ ] Switch with different stack height in branches (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpv_Copier.json)
- [ ] Switch with different stack height in branches, variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpv_variable_stack_Copier.json)

##### Combinations

- [ ] RJUMP and RJUMPI with the same target and equal stack height (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_Copier.json)
- [ ] RJUMP and RJUMPI with the same target and equal stack height in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_variable_stack_Copier.json)
- [ ] RJUMP and RJUMPI with the same target and different stack height (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_Copier.json)
- [ ] RJUMP and RJUMPI with the same target and different stack height in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpi_variable_stack_Copier.json)
- [ ] RJUMP and RJUMPV with the same target and equal stack height (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpv_Copier.json)
- [ ] RJUMP and RJUMPV with the same target and equal stack height in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpv_variable_stack_Copier.json)
- [ ] RJUMP and RJUMPV with the same target and different stack height (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpv_Copier.json)
- [ ] RJUMP and RJUMPV with the same target and different stack height in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/forwards_rjumpv_variable_stack_Copier.json)
- [ ] RJUMPI and RJUMPV with the same target

- [ ] RJUMP* to self (ethereum/tests: src/EOFTestsFiller/efStack/self_referencing_jumps_Copier.json)
- [ ] RJUMP* to self in a variable stack segment (ethereum/tests: src/EOFTestsFiller/efStack/self_referencing_jumps_variable_stack_Copier.json)

#### Stack underflow

- [ ] Stack underflows (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml )
- [ ] Stack underflow with enough items available in caller stack (ethereum/tests: src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [ ] Stack underflow in variable stack segment, only min underflow (ethereum/tests: src/EOFTestsFiller/efStack/underflow_variable_stack_Copier.json)
- [ ] Stack underflow in variable stack segment, both min and max underflow (ethereum/tests: src/EOFTestsFiller/efStack/underflow_variable_stack_Copier.json)

#### CALLF

- [ ] Valid CALLFs to functions with inputs (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml src/EOFTestsFiller/efStack/callf_stack_validation_Copier.json)
- [ ] CALLF stack underflows (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/EIP4750/validInvalidFiller.yml src/EOFTestsFiller/EIP5450/validInvalidFiller.yml src/EOFTestsFiller/efStack/callf_stack_validation_Copier.json)
- [ ] CALLF stack underflow in variable stack segment, only min underflow (ethereum/tests: src/EOFTestsFiller/efStack/underflow_variable_stack_Copier.json)
- [ ] CALLF stack underflow in variable stack segment, both min and max underflow (ethereum/tests: src/EOFTestsFiller/efStack/underflow_variable_stack_Copier.json)
- [ ] Branching to CALLFs with the same number of outputs (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)

#### RETF

- [ ] Valid RETF with correct number of items on stack (ethereum/tests: src/EOFTestsFiller/efStack/retf_stack_validation_Copier.json src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [ ] Invalid RETF with extra items on stack (ethereum/tests: src/EOFTestsFiller/efStack/retf_stack_validation_Copier.json ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [ ] RETF stack underflow (ethereum/tests: src/EOFTestsFiller/efStack/retf_stack_validation_Copier.json)
- [ ] RETF reached via different paths (ethereum/tests: src/EOFTestsFiller/efStack/retf_stack_validation_Copier.json)
- [ ] RETF in variable stack segment is not allowed (ethereum/tests: src/EOFTestsFiller/efStack/retf_variable_stack_Copier.json)
- [ ] Extra items on stack allowed for terminating instructions other than RETF (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)

#### JUMPF

- [ ] Extra items on stack are allowed for JUMPF to non-returning function (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_nonreturning_Copier.json src/EOFTestsFiller/efStack/jumpf_to_nonreturning_variable_stack_Copier.json)
- [ ] JUMPF stack underflows (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_nonreturning_Copier.json src/EOFTestsFiller/efStack/jumpf_to_returning_Copier.json)
- [ ] JUMPF stack underflow in a variable stack segment - only min underflow (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_nonreturning_variable_stack_Copier.json)
- [ ] JUMPF stack underflow in a variable stack segment - both min and max underflow (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_nonreturning_variable_stack_Copier.json)
- [ ] JUMPF into function with the same number of outputs (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_returning_Copier.json)
- [ ] JUMPF into function with fewer outputs than current one (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_returning_Copier.json)
- [ ] Extra items on stack are allowed for JUMPF to returning function (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_returning_Copier.json)
- [ ] JUMPF to returning in a variable stack segment is not allowed (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_returning_variable_stack_Copier.json)

#### Stack overflow

##### CALLF

- [ ] Max allowed stack height reached in CALLF-ed function (ethereum/tests: src/EOFTestsFiller/efStack/callf_stack_overflow_Copier.json)
- [ ] CALLF validation time stack overflow (ethereum/tests: src/EOFTestsFiller/EIP4750/validInvalidFiller.yml src/EOFTestsFiller/efStack/callf_stack_overflow_Copier.json)
- [ ] Max allowed stack height reached in CALLF-ed function with inputs (ethereum/tests: src/EOFTestsFiller/efStack/callf_with_inputs_stack_overflow_Copier.json)
- [ ] CALLF validation time stack overflow in function with inputs (ethereum/tests: src/EOFTestsFiller/EIP4750/validInvalidFiller.yml src/EOFTestsFiller/efStack/callf_with_inputs_stack_overflow_Copier.json)
- [ ] Max allowed stack height reached in CALLF-ed function. CALLF in variable stack segment. (ethereum/tests: src/EOFTestsFiller/efStack/callf_stack_overflow_variable_stack_Copier.json)
- [ ] CALLF validation time stack overflow in variable stack segment. (ethereum/tests: src/EOFTestsFiller/EIP4750/validInvalidFiller.yml src/EOFTestsFiller/efStack/callf_stack_overflow_variable_stack_Copier.json)
- [ ] Max allowed stack height reached in CALLF-ed function with inputs. CALLF in variable stack segment. (ethereum/tests: src/EOFTestsFiller/efStack/callf_with_inputs_stack_overflow_variable_stack_Copier.json)
- [ ] CALLF validation time stack overflow in function with inputs in variable stack segment. (ethereum/tests: src/EOFTestsFiller/EIP4750/validInvalidFiller.yml src/EOFTestsFiller/efStack/callf_with_inputs_stack_overflow_variable_stack_Copier.json)
- [ ] Function inputs are accessible and accounted for (no stack underflow if they are popped) (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)

##### JUMPF

- [ ] Max allowed stack height reached in JUMPF-ed function (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_stack_overflow_Copier.json)
- [ ] JUMPF validation time stack overflow (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_stack_overflow_Copier.json)
- [ ] Max allowed stack height reached in JUMPF-ed function with inputs
- [ ] JUMPF validation time stack overflow in function with inputs (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_with_inputs_stack_overflow_Copier.json)
- [ ] JUMPF validation time stack overflow in function with inputs, variable stack segment, only max overflow (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_with_inputs_stack_overflow_variable_stack_Copier.json)
- [ ] JUMPF validation time stack overflow in function with inputs, variable stack segment, both max and min overflow (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_with_inputs_stack_overflow_variable_stack_Copier.json)
- [ ] Max allowed stack height reached in JUMPF-ed function. JUMPF in variable stack segment. (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_stack_overflow_variable_stack_Copier.json)
- [ ] JUMPF validation time stack overflow in variable stack segment - only max overflow. (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_stack_overflow_variable_stack_Copier.json)
- [ ] JUMPF validation time stack overflow in variable stack segment - both min and max overflow. (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_stack_overflow_variable_stack_Copier.json)
- [ ] Max allowed stack height reached in JUMPF-ed function with inputs. JUMPF in variable stack segment.
- [ ] JUMPF validation time stack overflow in function with inputs in variable stack segment.

#### SWAPN/DUPN/EXCHANGE

- [ ] Valid DUPN with enough items on stack (ethereum/tests: src/EOFTestsFiller/efStack/dupn_stack_validation_Copier.json)
- [ ] DUPN stack underflow (ethereum/tests: src/EOFTestsFiller/efStack/dupn_stack_validation_Copier.json)
- [ ] Valid SWAPN with enough items on stack (ethereum/tests: src/EOFTestsFiller/efStack/swapn_stack_validation_Copier.json)
- [ ] SWAPN stack underflow (ethereum/tests: src/EOFTestsFiller/efStack/swapn_stack_validation_Copier.json)
- [ ] Valid EXCHANGE with enough items on stack (ethereum/tests: src/EOFTestsFiller/efStack/exchange_deep_stack_validation_Copier.json src/EOFTestsFiller/efStack/exchange_stack_validation_Copier.json)
- [ ] EXCHANGE stack underflow (ethereum/tests: src/EOFTestsFiller/efStack/exchange_stack_validation_Copier.json src/EOFTestsFiller/efStack/exchange_empty_stack_validation_Copier.json)

#### Other

- [ ] Wrong max_stack_height (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/efValidation/max_stack_height_Copier.json src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [ ] All opcodes correctly account for stack inputs/outputs (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [ ] Code reachable only via backwards jump is invalid
- [ ] Maximally broad [0, 1023] stack range (ethereum/tests: src/EOFTestsFiller/efStack/stack_range_maximally_broad_Copier.json)

### Execution

- [ ] Max stack size (1024) in CALLF-ed function (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP4200/EOF1_CALLF_ExecutionFiller.yml)


## EIP-6206: EOF - JUMPF and non-returning functions

### Validation

- [ ] 0 section returning (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [ ] 0 section declared non-returning but ends with RETF (ethereum/tests: src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [ ] CALLF into non-returning function (ethereum/tests: src/EOFTestsFiller/efValidation/callf_into_nonreturning_Copier.json)
- [ ] Valid JUMPF into sections with equal number of outputs (ethereum/tests: src/EOFTestsFiller/efValidation/jumpf_equal_outputs_Copier.json)
- [ ] Valid JUMPF into sections with different but compatible number of outputs (ethereum/tests: src/EOFTestsFiller/efValidation/jumpf_compatible_outputs_Copier.json)
- [ ] JUMPF into sections with incompatible outputs (ethereum/tests: src/EOFTestsFiller/efValidation/jumpf_incompatible_outputs_Copier.json)
- [ ] Non-returning section without JUMPF (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [ ] Non-returning section with JUMPF (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [ ] Returning section with RETF (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [ ] Returning section with JUMPF (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [ ] Returning section with JUMPF to returning and RETF (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [ ] Returning section with JUMPF to non-returning and RETF (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [ ] Invalid non-returning flag (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [ ] Circular JUMPF between two sections (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)

## EIP-7480: EOF - Data section access instructions

### Validation

- [ ] Valid DATALOADN with various offsets (ethereum/tests: src/EOFTestsFiller/efValidation/dataloadn_Copier.json)
- [ ] Truncated DATALOADN immediate (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_dataloadn_truncated_Copier.json)
- [ ] DATALOADN offset out of bounds (ethereum/tests: src/EOFTestsFiller/efValidation/dataloadn_Copier.json)
- [ ] DATALOADN accessing not full word (ethereum/tests: src/EOFTestsFiller/efValidation/dataloadn_Copier.json)

## EIP-663: SWAPN, DUPN and EXCHANGE instructions

### Validation

- [ ] A DUPN instruction causes stack overflow
- [ ] A DUPN instruction causes stack underflow
- [ ] A DUPN instruction causes max stack height mismatch
- [ ] A SWAPN instruction causes stack underflow

### Execution

- [x] Positive tests for DUPN instructions (./eip663_dupn_swapn_exchange/test_dupn.py::test_dupn_all_valid_immediates)
- [x] Positive tests for SWAPN instructions (./eip663_dupn_swapn_exchange/test_swapn.py::test_swapn_all_valid_immediates)

## EIP-7069: Revamped CALL instructions

### Execution

- [ ] EXTSTATICCALL from EOF to pure legacy contract (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_CallsFiller.yml)
- [ ] EXTSTATICCALL from EOF to non-pure legacy contract failing (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_CallsFiller.yml)
- [ ] EXTSTATICCALL from EOF to pure EOF contract (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_CallsFiller.yml)
- [ ] EXTSTATICCALL from EOF to non-pure EOF contract failing (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_CallsFiller.yml)


## EIP-7620: EOF Contract Creation

### Validation

- [ ] Valid EOFCREATEs referring to various container numbers (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_eofcreate_valid_Copier.json)
- [ ] Truncated before EOFCREATE immediate (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_eofcreate_invalid_Copier.json)
- [ ] EOFCREATE is not a valid terminating instruction (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_eofcreate_invalid_Copier.json)
- [ ] EOFCREATE immediate referring to non-existing container (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_eofcreate_invalid_Copier.json)
- [ ] EOFCREATE immediate referring to container with truncated data (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_eofcreate_invalid_Copier.json)
- [x] Valid RETURNCONTRACTs referring to various container numbers (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_returncontract_valid_Copier.json)
- [x] Truncated before RETURNCONTRACT immediate (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_returncontract_invalid_Copier.json)
- [x] RETURNCONTRACT immediate referring to non-existing container (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_returncontract_invalid_Copier.json)
- [x] Unreachable code after RETURNCONTRACT, check that RETURNCONTRACT is terminating (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_returncontract_invalid_Copier.json)

## EIP-7698: EOF - Creation transaction
