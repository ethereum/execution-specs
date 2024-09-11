# EOF Testing Coverage Tracker

- [ ] Example Test Case 1
- [x] Example Test Case 2 (`tests/prague/eip7692_eof_v1/eip3540_eof_v1test_example_valid_invalid.py::test_example_valid_invalid`)

## EIP-3540: EOF - EVM Object Format v1

### Validation

- [x] Empty code is not a valid EOF (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k empty_container`)
- [x] Valid container without data section (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k single_code_section_no_data_section`)
- [x] Valid container with data section (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_valid_containers -k single_code_section_with_data_section`)
- [x] Valid container with truncated data section (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k data_section_contents_incomplete`, `tests/prague/eip7692_eof_v1/eip3540_eof_v1test_migrated_valid_invalid.py::test_migrated_valid_invalid -k data_section_contents_incomplete`)
- [x] Valid container with data section truncated to empty (`tests/prague/eip7692_eof_v1/eip3540_eof_v1test_container_validation.py::test_invalid_containers -k no_data_section_contents`, `tests/prague/eip7692_eof_v1/eip3540_eof_v1test_migrated_valid_invalid.py::test_migrated_valid_invalid -k no_data_section_contents`)
- [x] Valid containers with multiple code sections (`tests/prague/eip7692_eof_v1/tests/prague/eip7692_eof_v1/eip3540_eof_v1test_container_validation.py::test_valid_containers -k multiple_code_sections`)
- [x] Valid containers with max number of code sections (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_max_code_sections`)
- [x] Too many code sections (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k too_many_code_sections`)
- [x] Truncated magic (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k incomplete_magic`)
- [x] Valid container except magic (`tests/prague/eip7692_eof_v1/eip3540_eof_v1test_container_validation.py::test_magic_validation`)
- [x] Truncated before version  (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k no_version`)
- [x] Valid container except version (`tests/prague/eip7692_eof_v1/eip3540_eof_v1test_container_validation.py::test_version_validation`)
- [x] Truncated before type section header (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k no_type_header`)
- [x] Truncated before type section size (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k no_type_section_size`)
- [x] Truncated type section size (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k incomplete_type_section_size`)
- [x] No type section header (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_section_order.py::test_section_order -k test_position_CasePosition.HEADER-section_test_SectionTest.MISSING-section_kind_TYPE`)
- [x] Truncated before code section header (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k no_code_header`)
- [x] Truncated before code section number (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k code_section_count_missing`)
- [x] Truncated code section number (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k code_section_count_incomplete`)
- [x] Truncated before code section size (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k code_section_size_missing`)
- [x] Truncated code section size (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k code_section_size_incomplete`)
- [x] No code section header (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_section_order.py::test_section_order -k test_position_CasePosition.HEADER-section_test_SectionTest.MISSING-section_kind_CODE`) 
- [x] Zero code section number (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k zero_code_sections_header`)
- [x] Zero code section size (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k empty_code_section`)
- [x] Zero code section size with non-empty data section (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k empty_code_section_with_non_empty_data`)
- [x] No container sections, truncated before data section header (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k truncated_header_data_section`)
- [x] Container sections present, truncated before data section header (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k truncated_header_data_section_with_container_section`)
- [x] Truncated before data section size (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k no_data_section_size`)
- [x] Truncated data section size (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k data_section_size_incomplete`)
- [x] Truncated before header terminator (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k terminator_incomplete`)
- [x] Truncated before type section (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k truncated_before_type_section`)
- [x] Type section truncated before outputs (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k truncated_type_section_before_outputs`)
- [x] Type section truncated before max_stack_height (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k truncated_type_section_before_max_stack_height`)
- [x] Type section truncated max_stack_height (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k truncated_type_section_truncated_max_stack_height`)
- [x] Truncated before code sections (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k no_code_section_contents`)
- [x] Truncated code section (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k incomplete_code_section_contents`)
- [x] Data section empty, trailing bytes (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k no_data_section_contents`)
- [x] Data section non-empty, trailing bytes (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k trailing_bytes_after_data_section`)
- [x] Wrong order of sections (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_section_order.py`)
- [x] No data section header (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_section_order.py::test_section_order -k test_position_CasePosition.HEADER-section_test_SectionTest.MISSING-section_kind_DATA`)
- [x] Multiple data sections (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k multiple_data_sections`, `tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k multiple_code_and_data_sections`)
- [x] Unknown section id (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k unknown_section_1`, `tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k unknown_section_2`)
- [x] Type section size != 4 * code section number (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k type_section_too`)
- [x] Code section with max max_stack_height (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_valid_containers -k single_code_section_max_stack_size`)
- [x] Code section with max_stack_height above limit (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_invalid_containers -k single_code_section_max_stack_size_too_large`)
- [x] Valid code sections with inputs/outputs (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k code_section_with_inputs_outputs`)
- [x] Valid code section with max inputs (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k code_section_input_maximum`)
- [x] Valid code section with max outputs (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k code_section_output_maximum`)
- [x] Code sections with invalid number of inputs/outputs (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k code_section_input_too_large`, `tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k code_section_output_too_large`)
- [x] First section with inputs/outputs (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k invalid_first_code_section`)
- [x] Multiple type section headers (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k too_many_type_sections`)
- [x] Multiple code section headers (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k multiple_code_headers`)
- [x] Multiple data section headers (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k multiple_data_sections`)
- [x] Container without type section (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_section_order.py::test_section_order -k 'SectionTest.MISSING-section_kind_TYPE'`)
- [x] Container without code sections (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_section_order.py::test_section_order -k 'SectionTest.MISSING-section_kind_CODE'`)
- [x] Container without data section (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_section_order.py::test_section_order -k 'SectionTest.MISSING-section_kind_DATA'`)
- [x] Valid containers without data section and with subcontainers (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_valid_containers[fork_CancunEIP7692-eof_test-single_subcontainer_without_data]`)
- [x] Valid containers with data section and with subcontainers (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_valid_containers[fork_CancunEIP7692-eof_test-single_subcontainer_with_data]`)
- [x] Valid container with maximum number of subcontainers (`tests/prague/eip7692_eof_v1/eip7620_eof_create/test_subcontainer_validation.py::test_wide_container[fork_CancunEIP7692-eof_test-256]`)
- [x] Container with number of subcontainers above the limit (`tests/prague/eip7692_eof_v1/eip7620_eof_create/test_subcontainer_validation.py::test_wide_container[fork_CancunEIP7692-eof_test-257]`)
- [x] Subcontainer section header truncated before subcontainer number (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k no_container_section_count`)
- [x] Subcontainer section header truncated before subcontainer size (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k incomplete_container_section_count`)
- [x] Truncated subcontainer size (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k no_container_section_size`, `tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k incomplete_container_section_size`)
- [x] Zero container section number (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k zero_container_section_count`)
- [x] Zero container section size (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k zero_size_container_section`)
- [x] Truncated container section body (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k no_container_section_contents`)
- [x] Multiple container section headers (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k multiple_container_headers`)
- [x] Invalid subcontainer (`tests/prague/eip7692_eof_v1/eip7620_eof_create/test_subcontainer_validation.py -k invalid`)
- [x] Invalid subcontainer on a deep nesting level (`tests/prague/eip7692_eof_v1/eip7620_eof_create/test_subcontainer_validation.py::test_deep_container`)
- [x] Max number of inputs/outputs in a section (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_valid_containers[fork_CancunEIP7692-eof_test-code_section_input_maximum]`, `tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py::test_valid_containers[fork_CancunEIP7692-eof_test-code_section_output_maximum]`)
- [x] Number of inputs/outputs in a section above the limit (`tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k code_section_input_too_large`, `tests/prague/eip7692_eof_v1/eip3540_eof_v1/test_container_validation.py -k code_section_output_too_large`)

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
- [ ] Unreachable code section that calls itself with JUMPF
- [ ] Unreachable code section that calls itself with CALLF
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
- [ ] Stack underflow with enough items available in caller stack - can't dig into caller frame (ethereum/tests: src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [ ] Stack underflow in variable stack segment, only min underflow (ethereum/tests: src/EOFTestsFiller/efStack/underflow_variable_stack_Copier.json)
- [ ] Stack underflow in variable stack segment, both min and max underflow (ethereum/tests: src/EOFTestsFiller/efStack/underflow_variable_stack_Copier.json)

#### CALLF

- [ ] Valid CALLFs to functions with inputs (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml src/EOFTestsFiller/efStack/callf_stack_validation_Copier.json)
- [ ] CALLF stack underflows (ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/EIP4750/validInvalidFiller.yml src/EOFTestsFiller/EIP5450/validInvalidFiller.yml src/EOFTestsFiller/efStack/callf_stack_validation_Copier.json)
- [ ] CALLF stack underflow in variable stack segment, only min underflow (ethereum/tests: src/EOFTestsFiller/efStack/underflow_variable_stack_Copier.json)
- [ ] CALLF stack underflow in variable stack segment, both min and max underflow (ethereum/tests: src/EOFTestsFiller/efStack/underflow_variable_stack_Copier.json)
- [ ] Branching to CALLFs with the same number of outputs (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [ ] Check that CALLF stack inputs/outputs equal to target section type definition

#### RETF

- [ ] Valid RETF with correct number of items on stack (ethereum/tests: src/EOFTestsFiller/efStack/retf_stack_validation_Copier.json src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [ ] Invalid RETF with extra items on stack (ethereum/tests: src/EOFTestsFiller/efStack/retf_stack_validation_Copier.json ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [ ] RETF stack underflow (ethereum/tests: src/EOFTestsFiller/efStack/retf_stack_validation_Copier.json)
- [ ] RETF reached via different paths (ethereum/tests: src/EOFTestsFiller/efStack/retf_stack_validation_Copier.json)
- [ ] RETF in variable stack segment is not allowed (ethereum/tests: src/EOFTestsFiller/efStack/retf_variable_stack_Copier.json)
- [ ] Extra items on stack allowed for terminating instructions other than RETF (ethereum/tests: src/EOFTestsFiller/EIP5450/validInvalidFiller.yml)
- [x] Invalid RETF in a non-returning function (`tests/prague/eip7692_eof_v1/eip6206_jumpf/test_nonretruning_validation.py::test_first_section_returning_code`)

#### JUMPF

- [ ] Extra items on stack are allowed for JUMPF to non-returning function (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_nonreturning_Copier.json src/EOFTestsFiller/efStack/jumpf_to_nonreturning_variable_stack_Copier.json)
- [ ] JUMPF stack underflows (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_nonreturning_Copier.json src/EOFTestsFiller/efStack/jumpf_to_returning_Copier.json)
- [ ] JUMPF stack underflow in a variable stack segment - only min underflow (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_nonreturning_variable_stack_Copier.json)
- [ ] JUMPF stack underflow in a variable stack segment - both min and max underflow (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_nonreturning_variable_stack_Copier.json)
- [ ] JUMPF into function with the same number of outputs (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_returning_Copier.json)
- [ ] JUMPF into function with fewer outputs than current one (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_returning_Copier.json)
- [ ] Extra items on stack are allowed for JUMPF to returning function (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_returning_Copier.json)
- [ ] JUMPF to returning in a variable stack segment is not allowed (ethereum/tests: src/EOFTestsFiller/efStack/jumpf_to_returning_variable_stack_Copier.json)
- [x] Invalid JUMPF in a non-returning function (`tests/prague/eip7692_eof_v1/eip6206_jumpf/test_nonretruning_validation.py::test_retf_in_nonreturning`)

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

- [x] Zero section returning (`tests/prague/eip7692_eof_v1/eip6206_jumpf/test_nonretruning_validation.py::test_first_section_returning` ethereum/tests: ./src/EOFTestsFiller/efExample/validInvalidFiller.yml src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [x] Zero section declared non-returning but ends with RETF (`tests/prague/eip7692_eof_v1/eip6206_jumpf/test_nonretruning_validation.py::test_retf_in_nonreturning` ethereum/tests: src/EOFTestsFiller/EIP4750/validInvalidFiller.yml)
- [ ] CALLF into non-returning function (ethereum/tests: src/EOFTestsFiller/efValidation/callf_into_nonreturning_Copier.json)
- [ ] Valid JUMPF into sections with equal number of outputs (ethereum/tests: src/EOFTestsFiller/efValidation/jumpf_equal_outputs_Copier.json)
- [ ] Valid JUMPF into sections with different but compatible number of outputs (ethereum/tests: src/EOFTestsFiller/efValidation/jumpf_compatible_outputs_Copier.json)
- [ ] JUMPF into sections with incompatible outputs (ethereum/tests: src/EOFTestsFiller/efValidation/jumpf_incompatible_outputs_Copier.json)
- [ ] Non-returning section without JUMPF (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [x] Non-returning section with JUMPF (`tests/prague/eip7692_eof_v1/eip6206_jumpf/test_nonretruning_validation.py::test_jumpf_in_nonreturning` ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [ ] Returning section with RETF (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [ ] Returning section with JUMPF (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [ ] Returning section with JUMPF to returning and RETF (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [ ] Returning section with JUMPF to non-returning and RETF (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [x] Returning section without JUMPF nor RETF (`tests/prague/eip7692_eof_v1/eip6206_jumpf/test_nonretruning_validation.py::test_returning_section_not_returning`)
- [ ] Invalid non-returning flag (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [ ] Circular JUMPF between two sections (ethereum/tests: src/EOFTestsFiller/efValidation/non_returning_status_Copier.json)
- [ ] JUMPF into non-existing section

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
- [x] Positive tests for EXCHANGE instruction (./eip663_dupn_swapn_exchange/test_exchange_py.py::test_exchange_all_valid_immediates)

## EIP-7069: Revamped CALL instructions

### Execution

- [x] EXTDELEGATECALL from EOF to EOF (evmone-tests: state_tests/state_transition/eof_calls/eof1_extdelegatecall_eof1.json)
- [x] EXTDELEGATECALL from EOF to legacy fails (evmone-tests: state_tests/state_transition/eof_calls/eof1_extdelegatecall_legacy.json)
- [ ] EXTSTATICCALL forwards static mode (evmone-tests: state_tests/state_transition/eof_calls/extdelegatecall_static.json)
- [x] EXTCALL with value success (evmone-tests: state_tests/state_transition/eof_calls/extcall_with_value.json)
- [ ] EXTCALL with value from EXTSTATICCALL (evmone-tests: state_tests/state_transition/eof_calls/extcall_static_with_value.json)
- [x] EXTCALL with value, not enough balance (evmone-tests: state_tests/state_transition/eof_calls/extcall_failing_with_value_balance_check.json)
- [ ] EXTCALL with value, check additional charge for value (evmone-tests: state_tests/state_transition/eof_calls/extcall_failing_with_value_additional_cost.json)
- [x] EXTCALL with gas not enough for callee to get 5000 gas (evmone-tests: state_tests/state_transition/eof_calls/extcall_min_callee_gas_failure_mode.json)
- [x] RETURNDATA* after EXTCALL (evmone-tests: state_tests/state_transition/eof_calls/extcall_output.json)
- [x] RETURNDATA* after EXTDELEGATECALL (evmone-tests: state_tests/state_transition/eof_calls/extdelegatecall_output.json state_tests/state_transition/eof_calls/extdelegatecall_returndatasize.json state_tests/state_transition/eof_calls/returndatacopy.json state_tests/state_transition/eof_calls/returndataload.json)
- [x] RETURNDATA* after EXTSTATICCALL (evmone-tests: state_tests/state_transition/eof_calls/extstaticcall_output.json)
- [x] RETURNDATA* after aborted EXT*CALL (evmone-tests: state_tests/state_transition/eof_calls/extdelegatecall_returndatasize_abort.json)
- [x] Failed EXTCALL clears returndata from previous EXTCALL (evmone-tests: state_tests/state_transition/eof_calls/extcall_clears_returndata.json)
- [ ] EXTCALL not enough gas for input memory charge (evmone-tests: state_tests/state_transition/eof_calls/extcall_memory.json)
- [ ] EXTDELEGATECALL not enough gas for input memory charge (evmone-tests: state_tests/state_transition/eof_calls/extdelegatecall_memory.json)
- [ ] EXTSTATICCALL not enough gas for input memory charge (evmone-tests: state_tests/state_transition/eof_calls/extstaticcall_memory.json)
- [x] EXTCALL exception due to target address overflow (bits set in high 12 bytes) (evmone-tests: state_tests/state_transition/eof_calls/extcall_ase_ready_violation.json)
- [x] EXTDELEGATECALL exception due to target address overflow (bits set in high 12 bytes) (evmone-tests: state_tests/state_transition/eof_calls/extdelegatecall_ase_ready_violation.json)
- [x] EXTSTATICCALL exception due to target address overflow (bits set in high 12 bytes) (evmone-tests: state_tests/state_transition/eof_calls/extstaticcall_ase_ready_violation.json)
- [ ] EXTCALL not enough gas for warming up target address (evmone-tests: state_tests/state_transition/eof_calls/extcall_cold_oog.json)
- [ ] EXTDELEGATECALL not enough gas for warming up target address (evmone-tests: state_tests/state_transition/eof_calls/extdelegatecall_cold_oog.json)
- [ ] EXTSTATICCALL not enough gas for warming up target address (evmone-tests: state_tests/state_transition/eof_calls/extstaticcall_cold_oog.json)
- [ ] EXTCALL not enough gas for account creation cost (transfer value to non-existing account) (evmone-tests: state_tests/state_transition/eof_calls/extcall_value_zero_to_nonexistent_account.json)
- [x] OOG after EXTCALL (evmone-tests: state_tests/state_transition/eof_calls/extcall_then_oog.json)
- [x] OOG after EXTDELEGATECALL (evmone-tests: state_tests/state_transition/eof_calls/extdelegatecall_then_oog.json)
- [x] OOG after EXTSTATICCALL (evmone-tests: state_tests/state_transition/eof_calls/extstaticcall_then_oog.json)
- [x] REVERT inside EXTCALL (evmone-tests: state_tests/state_transition/eof_calls/extcall_callee_revert.json)
- [x] REVERT inside EXTDELEGATECALL (evmone-tests: state_tests/state_transition/eof_calls/extdelegatecall_callee_revert.json)
- [x] REVERT inside EXTSTATICCALL (evmone-tests: state_tests/state_transition/eof_calls/extstaticcall_callee_revert.json)
- [x] EXTCALL with input (evmone-tests: state_tests/state_transition/eof_calls/extcall_input.json)
- [x] EXTDELEGATECALL with input (evmone-tests: state_tests/state_transition/eof_calls/extdelegatecall_input.json)
- [x] EXTSTATICCALL with input (evmone-tests: state_tests/state_transition/eof_calls/extstaticcall_input.json)
- [x] EXTCALL with just enough gas for MIN_RETAINED_GAS and MIN_CALLEE_GAS (evmone-tests: state_tests/state_transition/eof_calls/extcall_with_value_enough_gas.json)
- [x] EXTCALL with not enough gas for MIN_CALLEE_GAS (evmone-tests: state_tests/state_transition/eof_calls/extcall_with_value_low_gas.json)
- [ ] ADDRESS and CALLER inside EXTCALL (evmone-tests: state_tests/state_transition/eof_calls/extcall_recipient_and_code_address.json)
- [ ] ADDRESS and CALLER inside EXTDELEGATECALL (evmone-tests: state_tests/state_transition/eof_calls/extdelegatecall_recipient_and_code_address.json)
- [ ] ADDRESS and CALLER inside EXTSTATICCALL (evmone-tests: state_tests/state_transition/eof_calls/extstaticcall_recipient_and_code_address.json)
- [ ] Refund inside EXTCALL is applied after the transaction (evmone-tests: state_tests/state_transition/eof_calls/extcall_gas_refund_propagation.json)
- [ ] Refund inside EXTDELEGATECALL is applied after the transaction (evmone-tests: state_tests/state_transition/eof_calls/extdelegatecall_gas_refund_propagation.json)
- [x] EXTSTATICCALL from EOF to non-pure legacy contract failing (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_CallsFiller.yml)
- [x] EXTSTATICCALL from EOF to pure EOF contract (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_CallsFiller.yml)
- [x] EXTSTATICCALL from EOF to non-pure EOF contract failing (ethereum/tests: src/EIPTestsFiller/StateTests/stEOF/stEIP3540/EOF1_CallsFiller.yml)


## EIP-7620: EOF Contract Creation

### Validation

- [ ] Valid EOFCREATEs referring to various container numbers (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_eofcreate_valid_Copier.json)
- [ ] Truncated before EOFCREATE immediate (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_eofcreate_invalid_Copier.json)
- [ ] EOFCREATE is not a valid terminating instruction (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_eofcreate_invalid_Copier.json)
- [ ] EOFCREATE immediate referring to non-existing container (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_eofcreate_invalid_Copier.json)
- [ ] EOFCREATE immediate referring to container with truncated data (ethereum/tests: ./src/EOFTestsFiller/efValidation/EOF1_eofcreate_invalid_Copier.json)
- [x] Valid RETURNCONTRACTs referring to various container numbers (`tests/prague/eip7692_eof_v1/eip7620_eof_create/test_returncontract.py -k test_returncontract_valid_index`)
- [x] Truncated before RETURNCONTRACT immediate (`tests/prague/eip7692_eof_v1/eip7620_eof_create/test_returncontract.py::test_returncontract_invalid_truncated_immediate`)
- [x] RETURNCONTRACT immediate referring to non-existing container (`tests/prague/eip7692_eof_v1/eip7620_eof_create/test_returncontract.py -k test_returncontract_invalid_index`)
- [x] Unreachable code after RETURNCONTRACT, check that RETURNCONTRACT is terminating (`tests/prague/eip7692_eof_v1/eip7620_eof_create/test_returncontract.py::test_returncontract_terminating`)

### Execution

- [ ] CREATE with EOF initcode fails in Prague (evmone-tests: state_tests/state_transition/eof_create/create_with_eof_initcode.json)
- [ ] CREATE with EOF initcode fails in Cancun (evmone-tests: state_tests/state_transition/eof_create/create_with_eof_initcode_cancun.json)
- [ ] CREATE2 with EOF initcode fails in Prague (evmone-tests: state_tests/state_transition/eof_create/create2_with_eof_initcode.json)
- [ ] CREATE2 with EOF initcode fails in Cancun (evmone-tests: state_tests/state_transition/eof_create/create2_with_eof_initcode_cancun.json)
- [ ] CREATE with legacy initcode and EOF deploy code fails (evmone-tests: state_tests/state_transition/eof_create/create_deploying_eof.json)
- [ ] CREATE2 with legacy initcode and EOF deploy code fails (evmone-tests: state_tests/state_transition/eof_create/create2_deploying_eof.json)
- [ ] EOFCREATE success with empty aux data (evmone-tests: state_tests/state_transition/eof_create/eofcreate_empty_auxdata.json)
- [ ] EOFCREATE success with aux data length equal to declared in deploy container (evmone-tests: state_tests/state_transition/eof_create/eofcreate_auxdata_equal_to_declared.json)
- [ ] EOFCREATE success with aux data longer than size declared in deploy container (evmone-tests: state_tests/state_transition/eof_create/eofcreate_auxdata_longer_than_declared.json)
- [ ] EOFCREATE with aux data shorter than size declared in deploy container fails (evmone-tests: state_tests/state_transition/eof_create/eofcreate_auxdata_shorter_than_declared.json)
- [ ] EOFCREATE success deploying DATALOADN referring to aux data portion of deploy container data (evmone-tests: state_tests/state_transition/eof_create/eofcreate_dataloadn_referring_to_auxdata.json)
- [ ] EOFCREATE success with deploy container having aux data and subcontainer (evmone-tests: state_tests/state_transition/eof_create/eofcreate_with_auxdata_and_subcontainer.json)
- [ ] REVERT in initcontainer (evmone-tests: state_tests/state_transition/eof_create/eofcreate_revert_empty_returndata.json)
- [ ] REVERT with return data in initcontainer (evmone-tests: state_tests/state_transition/eof_create/eofcreate_revert_non_empty_returndata.json)
- [ ] Exceptional abort in initcontainer (evmone-tests: state_tests/state_transition/eof_create/eofcreate_initcontainer_aborts.json)
- [ ] EOFCREATE with deploy container of max size 0x6000 (evmone-tests: state_tests/state_transition/eof_create/eofcreate_deploy_container_max_size.json)
- [ ] EOFCREATE with deploy container size above limit (evmone-tests: state_tests/state_transition/eof_create/eofcreate_deploy_container_too_large.json)
- [ ] EOFCREATE with deploy container data size above 64K after appending aux data (evmone-tests: state_tests/state_transition/eof_create/eofcreate_appended_data_size_larger_than_64K.json)
- [ ] EOFCREATE with deploy container size above limit after appending aux data (evmone-tests: state_tests/state_transition/eof_create/eofcreate_deploy_container_with_aux_data_too_large.json)
- [ ] EOFCREATE success nested in EOFCREATE initcode (evmone-tests: state_tests/state_transition/eof_create/eofcreate_nested_eofcreate.json)
- [ ] EOFCREATE success nested in EOFCREATE initcode that reverts (evmone-tests: state_tests/state_transition/eof_create/eofcreate_nested_eofcreate_revert.json)
- [ ] EOFCREATE with value success
- [ ] EOFCREATE with value - not enough caller balance (evmone-tests: state_tests/state_transition/eof_create/eofcreate_caller_balance_too_low.json)
- [ ] EOFCREATE not enough gas for initcode (EIP-3860) charge (evmone-tests: state_tests/state_transition/eof_create/eofcreate_not_enough_gas_for_initcode_charge.json)
- [ ] EOFCREATE not enough gas for input memory expansion (evmone-tests: state_tests/state_transition/eof_create/eofcreate_not_enough_gas_for_mem_expansion.json)
- [ ] RETURNCONTRACT not enough gas for aux data memory expansion (evmone-tests: state_tests/state_transition/eof_create/returncontract_not_enough_gas_for_mem_expansion.json)
- [ ] Successful EOFCREATE clears returndata  (evmone-tests: state_tests/state_transition/eof_create/eofcreate_clears_returndata.json)
- [ ] Second EOFCREATE with the same container and salt fails (evmone-tests: state_tests/state_transition/eof_create/eofcreate_failure_after_eofcreate_success.json)
- [ ] Call created contract after EOFCREATE (evmone-tests: state_tests/state_transition/eof_create/eofcreate_call_created_contract.json)

## EIP-7698: EOF - Creation transaction

### Execution

- [ ] Creation transaction success with empty deploy container data (evmone-tests: state_tests/state_transition/eof_create/creation_tx.json)
- [ ] Creation transaction success with data in deploy container without aux data (evmone-tests: state_tests/state_transition/eof_create/creation_tx_deploy_data.json)
- [ ] Creation transaction success with data in deploy container with aux data length equal to declared (evmone-tests: state_tests/state_transition/eof_create/creation_tx_static_auxdata_in_calldata.json)
- [ ] Creation transaction success with data in deploy container with aux data longer than declared (evmone-tests: state_tests/state_transition/eof_create/creation_tx_dynamic_auxdata_in_calldata.json)
- [ ] Creation transaction success deploying DATALOADN referring to aux data portion of deploy container data (evmone-tests: state_tests/state_transition/eof_create/creation_tx_dataloadn_referring_to_auxdata.json)
- [ ] Exceptional abort in creation transaction initcode (evmone-tests: state_tests/state_transition/eof_create/creation_tx_initcontainer_aborts.json)
- [ ] RETURN in creation transaction initcode fails (evmone-tests: state_tests/state_transition/eof_create/creation_tx_initcontainer_return.json)
- [ ] STOP in creation transaction initcode fails (evmone-tests: state_tests/state_transition/eof_create/creation_tx_initcontainer_stop.json)
- [ ] Creation transaction with initcode of max allowed size 0xc000 (evmone-tests: state_tests/state_transition/eof_create/creation_tx_initcontainer_max_size.json)
- [ ] Creation transaction with initcode size above limit (evmone-tests: state_tests/state_transition/eof_create/creation_tx_initcontainer_too_large.json)
- [ ] Creation transaction deploys container of max allowed size 0x6000 (evmone-tests: state_tests/state_transition/eof_create/creation_tx_deploy_container_max_size.json)
- [ ] Creation transaction deploying container of size above limit fails (evmone-tests: state_tests/state_transition/eof_create/creation_tx_deploy_container_too_large.json)
- [ ] EOFCREATE success nested in creation transaction initcode (evmone-tests: state_tests/state_transition/eof_create/creation_tx_nested_eofcreate.json)
- [ ] Creation transaction with invalid initcontainer (invalid header) (evmone-tests: state_tests/state_transition/eof_create/creation_tx_invalid_initcode_header.json)
- [ ] Creation transaction with invalid initcontainer (invalid EOF version) (evmone-tests: state_tests/state_transition/eof_create/creation_tx_invalid_eof_version.json)
- [ ] Creation transaction with invalid initcontainer (invalid max stack height) (evmone-tests: state_tests/state_transition/eof_create/creation_tx_invalid_initcode.json)
- [ ] Creation transaction fails if initcontainer has truncated data section (declared size > present data size ) (evmone-tests: state_tests/state_transition/eof_create/creation_tx_truncated_data_initcode.json)
- [ ] Creation transaction with invalid deploy container (evmone-tests: state_tests/state_transition/eof_create/creation_tx_invalid_deploycode.json)
- [ ] Create transaction with legacy initcode and EOF deploy code fails (evmone-tests: state_tests/state_transition/eof_create/creation_tx_deploying_eof.json)
- [ ] EOF creation transaction fails before Prague (evmone-tests: state_tests/state_transition/eof_create/initcode_transaction_before_prague.json)
