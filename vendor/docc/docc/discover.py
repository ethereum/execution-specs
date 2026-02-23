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
Discovery is the process of finding sources.
"""

from abc import ABC, abstractmethod
from typing import FrozenSet, Iterator, Sequence, Tuple, TypeVar

from .plugins.loader import Loader
from .settings import PluginSettings, Settings
from .source import Source

T = TypeVar("T", bound=Source)


class Discover(ABC):
    """
    Finds sources for which to generate documentation.
    """

    @abstractmethod
    def __init__(self, config: PluginSettings) -> None:
        """
        Construct a new instance with the given configuration.
        """
        raise NotImplementedError()

    @abstractmethod
    def discover(self, known: FrozenSet[T]) -> Iterator[Source]:
        """
        Find sources.
        """
        raise NotImplementedError()


def load(settings: Settings) -> Sequence[Tuple[str, Discover]]:
    """
    Load the discovery plugins as requested in settings.
    """
    loader = Loader()

    sources = []

    for name in settings.discovery:
        class_ = loader.load(Discover, name)
        plugin_settings = settings.for_plugin(name)
        sources.append((name, class_(plugin_settings)))

    return sources
