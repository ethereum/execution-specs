# Copyright (C) 2022-2023 Ethereum Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Timing measurement utilities.
"""

import logging
import time
from contextlib import contextmanager
from typing import Iterator


@contextmanager
def measure(
    message: str,
    level: int = logging.DEBUG,
) -> Iterator[None]:
    """
    Log how long a block took to execute.
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
        logging.log(level, message, end - start)
