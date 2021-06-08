
ETHEREUM_TEST_PATH=$(CURDIR)
export ETHEREUM_TEST_PATH

# travis error on stChangedEIP150 removed folder name for some reason. can't reproduce locally 
tx_tests:=$(wildcard TransactionTests/*)
gs_tests:=$(filter-out %stEWASMTests %stChangedEIP150 %stEIP2930 %stSubroutine %stEIP2537, $(wildcard GeneralStateTests/*))
bc_tests:=$(wildcard BlockchainTests/*)
vm_tests:=$(wildcard VMTests/*)
all_tests:=$(gs_tests) $(bc_tests) $(vm_tests)

tx_fillers:=$(wildcard src/TransactionTestsFiller/*.json)
gs_fillers:=$(wildcard src/GeneralStateTestsFiller/*.json)
bc_fillers:=$(wildcard src/BlockchainTestsFiller/*.json)
vm_fillers:=$(filter-out %.sol %.md, $(wildcard src/VMTestsFiller/*))
all_fillers:=$(gs_fillers) $(bc_fillers) $(vm_fillers)

all_schemas:=$(wildcard JSONSchema/*.json)

# Testset sanitation
sani: sani-schema sani-vm sani-gs sani-tx sani-bc

sani-schema: $(all_schemas:=.format)

sani-vm: $(vm_tests:=.format) $(vm_fillers:=.format) \
         $(vm_tests:=.valid)  $(vm_fillers:=.valid)  \
         $(vm_tests:=.filled)

# TODO: enable $(gs_fillers:=.valid) $(gs_tests:=.format) $(gs_fillers:=.format)
sani-gs: $(gs_tests:=.valid) # $(gs_tests:=.filled)

# TODO: enable $(tx_tests:=.format) $(tx_fillers:=.format) $(tx_tests:=.valid) $(tx_fillers:=.valid)
sani-tx: $(tx_tests:=.filled)

# TODO: enable $(bc_tests:=.format) $(bc_fillers:=.format) $(bc_tests:=.filled)
sani-bc: $(bc_tests:=.valid)  # $(bc_fillers:=.valid)

%.format:
	python3 test.py format ./$*
	git diff --quiet --exit-code &>/dev/null

%.valid:
	python3 test.py validate ./$*

%.filled:
	python3 test.py checkFilled ./$*

# Test running command

run-tests:=$(all-tests:=.test)
run: $(run-tests)

%.run:
	testeth -t $* -- --verbosity 2

# Test filling command

fill-tests:=$(all-tests:=.fill)
fill: $(fill-tests)

%.fill:
	testeth -t $* -- --filltests --verbosity 2 --all
	python3 test.py format ./$*
