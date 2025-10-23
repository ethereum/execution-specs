"""A standard interface for interactive CLI inputs."""

from .questionary_input_repository import QuestionaryInputRepository

# Instantiate the input repository
input_repository = QuestionaryInputRepository()


def input_text(question: str) -> str:
    """
    Ask a simple text input question.

    Args:
        question (str): The question to ask.

    Returns:
        str: The user's response.

    """
    return input_repository.input_text(question)


def input_password(question: str) -> str:
    """
    Ask a password input question (hidden text).

    Args:
        question (str): The question to ask.

    Returns:
        str: The user's response (password).

    """
    return input_repository.input_password(question)


def input_select(question: str, choices: list) -> str:
    """
    Ask a single-choice question from a list of options.

    Args:
        question (str): The question to ask.
        choices (list): A list of options for the user to choose from.

    Returns:
        str: The selected choice.

    """
    return input_repository.input_select(question, choices)


def input_checkbox(question: str, choices: list) -> list:
    """
    Ask a multi-choice question and return a list of selected choices.

    Args:
        question (str): The question to ask.
        choices (list): A list of options for the user to choose from.

    Returns:
        list: The list of selected choices.

    """
    return input_repository.input_checkbox(question, choices)


def input_confirm(question: str) -> bool:
    """
    Ask a yes/no confirmation question.

    Args:
        question (str): The question to ask.

    Returns:
        bool: True for 'yes', False for 'no'.

    """
    return input_repository.input_confirm(question)
