import pytest
from ethereum_spec_tools.evm_tools.t8n.transition_tool import EELST8N
from ethereum_clis import TransitionTool


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    TransitionTool.set_default_tool(EELST8N)
