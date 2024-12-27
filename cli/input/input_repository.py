"""An abstract base class for handling interactive CLI inputs."""

from abc import ABC, abstractmethod
from typing import List


class InputRepository(ABC):
    """
    Abstract base class for input handling.
    This class defines the interface for different input types that can be swapped out.
    """

    @abstractmethod
    def input_text(self, question: str) -> str:
        """Ask a text input question."""
        pass

    @abstractmethod
    def input_password(self, question: str) -> str:
        """Ask a password input question (hidden)."""
        pass

    @abstractmethod
    def input_select(self, question: str, choices: List[str]) -> str:
        """Ask a single-choice selection question."""
        pass

    @abstractmethod
    def input_checkbox(self, question: str, choices: List[str]) -> List[str]:
        """Ask a multi-choice question."""
        pass

    @abstractmethod
    def input_confirm(self, question: str) -> bool:
        """Ask a yes/no confirmation question."""
        pass
