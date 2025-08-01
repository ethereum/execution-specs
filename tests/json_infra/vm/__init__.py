from ..conftest import pytest_config

FORKS = [
    ("ConstantinopleFix", "constantinople"),
    ("Byzantium", "byzantium"),
    ("EIP158", "spurious_dragon"),
    ("EIP150", "tangerine_whistle"),
    ("Homestead", "homestead"),
    ("Frontier", "frontier"),
]


# Determine which forks to generate tests for
if pytest_config and pytest_config.getoption("fork", None):
    # If --fork option is specified, only generate test for that fork
    fork_option = pytest_config.getoption("fork")
    has_vm_tests = False
    for fork in FORKS:
        if fork[0] == fork_option:
            has_vm_tests = True
            forks_to_test = [fork]
            break
    if not has_vm_tests:
        forks_to_test = []
else:
    # If no --fork option, generate tests for all forks
    forks_to_test = FORKS
