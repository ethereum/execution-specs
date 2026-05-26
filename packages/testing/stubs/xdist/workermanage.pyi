from typing import Any

import pytest

class WorkerController:
    config: pytest.Config
    workeroutput: dict[str, Any]
