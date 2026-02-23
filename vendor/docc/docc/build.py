# Copyright (C) 2022-2024 Ethereum Foundation
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
Implementations of `Builder` convert each `Source` into a `Document`.
"""

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from types import TracebackType
from typing import Dict, Iterator, Optional, Set, Tuple, Type

from .document import Document
from .plugins.loader import Loader
from .settings import PluginSettings, Settings
from .source import Source


class Builder(AbstractContextManager["Builder", None], ABC):
    """
    Consumes unprocessed `Source` instances and creates `Document`s.
    """

    @abstractmethod
    def __init__(self, config: PluginSettings) -> None:
        """
        Create a Builder with the given configuration.
        """
        raise NotImplementedError()

    @abstractmethod
    def build(
        self,
        unprocessed: Set[Source],
        processed: Dict[Source, Document],
    ) -> None:
        """
        Consume unprocessed Sources and insert their Documents into processed.
        """
        raise NotImplementedError()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Context handler clean-up function.
        """


def load(settings: Settings) -> Iterator[Tuple[str, Builder]]:
    """
    Load the builder plugins as requested in settings.
    """
    loader = Loader()

    for name in settings.build:
        class_ = loader.load(Builder, name)
        plugin_settings = settings.for_plugin(name)
        yield (name, class_(plugin_settings))
