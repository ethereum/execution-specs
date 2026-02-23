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
Transforms modify Documents.
"""

from abc import ABC, abstractmethod
from typing import Sequence, Tuple

from .context import Context
from .plugins.loader import Loader
from .settings import PluginSettings, Settings


class Transform(ABC):
    """
    Applies a transformation to a Document.
    """

    @abstractmethod
    def __init__(self, config: PluginSettings) -> None:
        """
        Create a Transform with the given configuration.
        """
        raise NotImplementedError()

    @abstractmethod
    def transform(self, context: Context) -> None:
        """
        Apply the transformation to the given document.
        """
        raise NotImplementedError()


def load(settings: Settings) -> Sequence[Tuple[str, Transform]]:
    """
    Load the transform plugins as requested in settings.
    """
    loader = Loader()

    sources = []

    for name in settings.transform:
        class_ = loader.load(Transform, name)
        plugin_settings = settings.for_plugin(name)
        sources.append((name, class_(plugin_settings)))

    return sources
