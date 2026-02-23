# Copyright (C) 2023 Ethereum Foundation
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
Additional context provided alongside a Document.
"""

from abc import ABC, abstractmethod
from typing import Generic, Iterator, Mapping, Optional, Tuple, Type, TypeVar

from .plugins.loader import Loader
from .settings import PluginSettings, Settings

Q = TypeVar("Q")


class Context:
    """
    A single "unit" of transformation, typically containing a Document and
    Source, among other things.
    """

    __slots__ = ("_items",)

    _items: Mapping[Type[object], object]

    def __init__(
        self, items: Optional[Mapping[Type[object], object]] = None
    ) -> None:
        if items is None:
            items = {}

        for key, value in items.items():
            if not isinstance(value, key):
                raise ValueError(f"`{value}` is not an instance of `{key}`")

        self._items = items

    def __contains__(self, class_: Type[Q]) -> bool:
        """
        `True` if the Context contains `class_`, `False` otherwise.
        """
        return class_ in self._items

    def __getitem__(self, class_: Type[Q]) -> Q:
        """
        Given a type, return an instance of that type if one has been stored in
        this Context.

        For example:

        ```python
        document = context[Document]
        ```
        """
        item = self._items[class_]
        assert isinstance(item, class_)
        return item

    def __repr__(self) -> str:
        """
        Returns a string representation of this object.
        """
        return f"{self.__class__.__name__}({self._items!r})"


R_co = TypeVar("R_co", covariant=True)


class Provider(ABC, Generic[R_co]):
    """
    Creates objects to be inserted into Context instances.
    """

    @classmethod
    @abstractmethod
    def provides(class_) -> Type[R_co]:
        """
        Return the type to be used as the key in the Context.
        """

    @abstractmethod
    def __init__(self, config: PluginSettings) -> None:
        """
        Create a Provider with the given configuration.
        """

    @abstractmethod
    def provide(self) -> R_co:
        """
        Create the object to be inserted into the Context.
        """


def load(settings: Settings) -> Iterator[Tuple[str, Provider[object]]]:
    """
    Load the context plugins as requested in settings.
    """
    loader = Loader()

    for name in settings.context:
        class_ = loader.load(Provider, name)
        plugin_settings = settings.for_plugin(name)
        yield (name, class_(plugin_settings))
