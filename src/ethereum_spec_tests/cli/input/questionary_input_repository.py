"""
Interactive CLI inputs using questionary library.
See: https://questionary.readthedocs.io/.
"""

from questionary import checkbox, confirm, password, select, text

from .input_repository import InputRepository


class QuestionaryInputRepository(InputRepository):
    """Repository for handling various types of user inputs using the Questionary library."""

    def input_text(self, question: str) -> str:
        """Ask a text input question."""
        return text(message=question).ask()

    def input_password(self, question: str) -> str:
        """Ask a password input question (hidden)."""
        return password(message=question).ask()

    def input_select(self, question: str, choices: list) -> str:
        """Ask a single-choice selection question."""
        return select(message=question, choices=choices).ask()

    def input_checkbox(self, question: str, choices: list) -> list:
        """Ask a multi-choice question."""
        return checkbox(message=question, choices=choices).ask()

    def input_confirm(self, question: str) -> bool:
        """Ask a yes/no confirmation question."""
        return confirm(message=question).ask()
