"""
Test timing class used to time tests.
"""

import time
from typing import List


class TimingData:
    """
    The times taken to perform the various steps of a test case (seconds).
    """

    name: str
    start_time: float | None
    end_time: float | None
    parent: "TimingData | None"
    timings: "List[TimingData]"

    def __init__(self, name: str, parent: "TimingData | None" = None):
        """
        Initialize the timing data.
        """
        self.name = name
        self.start_time = None
        self.end_time = None
        self.parent = parent
        self.timings = []

    @staticmethod
    def format_float(num: float | None, precision: int = 4) -> str | None:
        """
        Format a float to a specific precision in significant figures.
        """
        if num is None:
            return None
        return f"{num:.{precision}f}"

    def __enter__(self):
        """
        Start timing the test case.
        """
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Record the time taken since the last time recorded.
        """
        self.end_time = time.perf_counter()

    def time(self, sub_name: str) -> "TimingData":
        """
        Record the time taken in an execution section.
        """
        new_timing = TimingData(sub_name, self)
        self.timings.append(new_timing)
        return new_timing

    def formatted(self, precision: int = 4, indent: int = 0) -> str:
        """
        Recursively format the timing data with correct indentation
        """
        assert self.start_time is not None
        assert self.end_time is not None
        formatted = (
            f"{' ' * indent}{self.name}: "
            f"{TimingData.format_float(self.end_time - self.start_time, precision)}\n"
        )
        for timing in self.timings:
            formatted += timing.formatted(precision, indent + 2)
        return formatted
