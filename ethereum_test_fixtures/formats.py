"""
Fixture formats enum.
"""
from enum import Enum
from pathlib import Path


class FixtureFormats(Enum):
    """
    Helper class to define fixture formats.
    """

    UNSET_TEST_FORMAT = "unset_test_format"
    STATE_TEST = "state_test"
    BLOCKCHAIN_TEST = "blockchain_test"
    BLOCKCHAIN_TEST_ENGINE = "blockchain_test_engine"
    EOF_TEST = "eof_test"

    @classmethod
    def is_state_test(cls, format):  # noqa: D102
        return format == cls.STATE_TEST

    @classmethod
    def is_blockchain_test(cls, format):  # noqa: D102
        return format in (cls.BLOCKCHAIN_TEST, cls.BLOCKCHAIN_TEST_ENGINE)

    @classmethod
    def is_hive_format(cls, format):  # noqa: D102
        return format == cls.BLOCKCHAIN_TEST_ENGINE

    @classmethod
    def is_standard_format(cls, format):  # noqa: D102
        return format in (cls.STATE_TEST, cls.BLOCKCHAIN_TEST)

    @classmethod
    def is_verifiable(cls, format):  # noqa: D102
        return format in (cls.STATE_TEST, cls.BLOCKCHAIN_TEST)

    @classmethod
    def get_format_description(cls, format):
        """
        Returns a description of the fixture format.

        Used to add a description to the generated pytest marks.
        """
        if format == cls.UNSET_TEST_FORMAT:
            return "Unknown fixture format; it has not been set."
        elif format == cls.STATE_TEST:
            return "Tests that generate a state test fixture."
        elif format == cls.BLOCKCHAIN_TEST:
            return "Tests that generate a blockchain test fixture."
        elif format == cls.BLOCKCHAIN_TEST_ENGINE:
            return "Tests that generate a blockchain test fixture in Engine API format."
        elif format == cls.EOF_TEST:
            return "Tests that generate an EOF test fixture."
        raise Exception(f"Unknown fixture format: {format}.")

    @property
    def output_base_dir_name(self) -> Path:
        """
        Returns the name of the subdirectory where this type of fixture should be dumped to.
        """
        return Path(self.value.replace("test", "tests"))

    @property
    def output_file_extension(self) -> str:
        """
        Returns the file extension for this type of fixture.

        By default, fixtures are dumped as JSON files.
        """
        return ".json"
