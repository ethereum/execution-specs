"""
Ethereum Specs EVM Transition tool interface.

https://github.com/ethereum/execution-specs
"""

from pathlib import Path
from re import compile

from ethereum_test_forks import Constantinople, ConstantinopleFix, Fork

from .geth import GethTransitionTool

UNSUPPORTED_FORKS = (
    Constantinople,
    ConstantinopleFix,
)


class ExecutionSpecsTransitionTool(GethTransitionTool):
    """
    Ethereum Specs `ethereum-spec-evm` Transition tool interface wrapper class.

    The behavior of this tool is almost identical to go-ethereum's `evm t8n` command.

    note: How to use the `ethereum-spec-evm` tool:

        1. Create a virtual environment and activate it:
            ```
            python -m venv venv
            source venv/bin/activate
            ```
        2. Clone the ethereum/execution-specs repository and change working directory to it:
            ```
            git clone git@github.com:ethereum/execution-specs.git
            cd execution-specs
            ```
        3. Install the packages provided by the repository:
            ```
            pip install -e .
            ```
            Check that the `ethereum-spec-evm` command is available:
            ```
            ethereum-spec-evm --help
            ```
        4. Clone the ethereum/execution-specs-tests repository and change working directory to it:
            ```
            cd ..
            git clone git@github.com:ethereum/execution-spec-tests.git
            cd execution-spec-tests
            ```
        5. Install the packages provided by the ethereum/execution-spec-tests repository:
            ```
            pip install -e .
            ```
        6. Run the tests, specifying the `ethereum-spec-evm` command as the transition tool:
            ```
            fill --evm-bin=ethereum-spec-evm
            ```
    """

    default_binary = Path("ethereum-spec-evm")
    detect_binary_pattern = compile(r"^ethereum-spec-evm\b")

    def is_fork_supported(self, fork: Fork) -> bool:
        """
        Returns True if the fork is supported by the tool.
        Currently, ethereum-spec-evm provides no way to determine supported forks.
        """
        return fork not in UNSUPPORTED_FORKS
