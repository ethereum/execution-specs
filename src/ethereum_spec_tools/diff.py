#!/usr/bin/env python3

"""
Generates diffs between Ethereum hardforks documentation.
"""

import os.path
import pickle
import re
from gzip import GzipFile
from multiprocessing import Pool
from typing import IO, Any, Iterator, List, Tuple, TypeVar, cast

import rstdiff
from docutils import SettingsSpec
from docutils.utils import new_document, new_reporter

from ethereum_spec_tools.forks import Hardfork

T = TypeVar("T")


def window(forks: List[T], window_size: int = 2) -> Iterator[List[T]]:
    """
    Group a list into overlapping chunks.
    """
    for i in range(len(forks) - window_size + 1):
        yield forks[i : i + window_size]


def find_pickles(path: str, extension: str) -> Iterator[str]:
    """
    Find files ending with :code:`extension`.
    """
    for directory, _, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith(extension):
                file_path = os.path.join(directory, filename)
                file_path = file_path[len(path) + 1 :]
                yield file_path


pattern = re.compile(r"[\n\t\s]")


def meaningful_diffs(
    old: Any,
    new: Any,
    trivial_changes: List[Tuple[str, str, re.RegexFlag]],
) -> bool:
    """Find if there are meaningful differences between the docs"""
    old = pattern.sub(" ", str(old))
    new = pattern.sub(" ", str(new))

    for old_word, new_word, flag in trivial_changes:
        old = re.sub(old_word, "", old, flags=flag)
        new = re.sub(new_word, "", new, flags=flag)

    return old != new


def _diff(
    trivial_changes: List[Tuple[str, str, re.RegexFlag]],
    ignore_in_name: List[str],
    old_path: str,
    new_path: str,
    diff_path: str,
    input_path: str,
    output_path: str,
    diff_index_path: str,
    pickles_len: int,
    count: int,
    pickle_path: str,
) -> None:
    old_pickle_path = os.path.join(old_path, pickle_path)
    new_pickle_path = os.path.join(new_path, pickle_path)

    try:
        with GzipFile(old_pickle_path, "rb") as old_file:
            old_doc = pickle.load(cast(IO[bytes], old_file))  # typeshed/2580
    except FileNotFoundError:
        old_doc = new_document(old_pickle_path)
        old_pickle_path = os.devnull

    try:
        with GzipFile(new_pickle_path, "rb") as new_file:
            new_doc = pickle.load(cast(IO[bytes], new_file))  # typeshed/2580
    except FileNotFoundError:
        new_doc = new_document(new_pickle_path)
        new_pickle_path = os.devnull

    if not meaningful_diffs(old_doc, new_doc, trivial_changes):
        return

    diff_pickle_path = os.path.join(diff_path, pickle_path + "64")

    diff_dir_path = os.path.dirname(diff_pickle_path)

    os.makedirs(diff_dir_path, exist_ok=True)

    print(
        "diff",
        old_pickle_path[len(input_path) :],
        "->",
        new_pickle_path[len(input_path) :],
    )

    pub = rstdiff.processCommandLine()

    pub.set_writer("picklebuilder.writers.pickle64")

    settings_spec = SettingsSpec()
    settings_spec.settings_spec = rstdiff.settings_spec
    settings_spec.settings_defaults = rstdiff.settings_defaults
    pub.process_command_line(
        usage=rstdiff.usage,
        description=rstdiff.description,
        settings_spec=settings_spec,
        config_section=rstdiff.config_section,
    )
    pub.set_destination(destination_path=diff_pickle_path)
    pub.set_reader("standalone", None, "restructuredtext")
    pub.settings.language_code = "en"  # TODO
    pub.settings.ignore_in_section_name = ignore_in_name

    old_doc.settings = pub.settings
    old_doc.reporter = new_reporter("RSTDIFF", pub.settings)

    new_doc.settings = pub.settings
    new_doc.reporter = new_reporter("RSTDIFF", pub.settings)

    rstdiff.Text2Words(old_doc).apply()
    rstdiff.Text2Words(new_doc).apply()

    try:
        diff_doc = rstdiff.createDiff(pub, old_doc, new_doc)
    except rstdiff.DocumentUnchanged:
        return

    rstdiff.Words2Text(diff_doc).apply()
    rstdiff.Generated2Inline(diff_doc).apply()

    pub.writer.write(diff_doc, pub.destination)
    pub.writer.assemble_parts()


def diff(
    output_path: str, input_path: str, old: Hardfork, new: Hardfork
) -> None:
    """
    Calculate the structured diff between two hardforks.
    """
    trivial_changes = [
        (
            old.short_name.replace("_", ".*?"),
            new.short_name.replace("_", ".*?"),
            re.I,
        ),
    ]

    ignore_in_name = old.short_name.split("_") + new.short_name.split("_")

    old_path = old.name.replace(".", os.sep)
    old_path = os.path.join(input_path, old_path)

    new_path = new.name.replace(".", os.sep)
    new_path = os.path.join(input_path, new_path)

    diff_path = old.short_name + "_" + new.short_name
    diff_index_file = diff_path + ".rst"
    diff_path = os.path.join(output_path, diff_path)

    diff_index_path = os.path.join(output_path, diff_index_file)
    diff_index_title = old.title_case_name + " \u2192 " + new.title_case_name

    index_path = os.path.join(output_path, "index.rst")

    with open(index_path, "a") as f:
        f.write(f"   {diff_index_file}\n")

    old_pickles = set(find_pickles(old_path, ".pickle"))
    new_pickles = set(find_pickles(new_path, ".pickle"))

    pickles = old_pickles | new_pickles

    with Pool() as pool:

        args = (
            (
                trivial_changes,
                ignore_in_name,
                old_path,
                new_path,
                diff_path,
                input_path,
                output_path,
                diff_index_path,
                len(pickles),
                c,
                p,
            )
            for (c, p) in enumerate(pickles, start=1)
        )

        pool.starmap(_diff, args)

    with open(diff_index_path, "w") as f:
        f.write("=" * len(diff_index_title) + "\n")
        f.write(diff_index_title + "\n")
        f.write("=" * len(diff_index_title) + "\n\n")

        f.write(".. toctree::\n")
        f.write("   :maxdepth: 1\n\n")

        for diff_file in sorted(list(find_pickles(diff_path, ".pickle64"))):
            f.write(
                f"   {os.path.join(os.path.basename(diff_path), diff_file)}\n"
            )


def main() -> None:
    """
    Compute structural diffs between hard forks.
    """
    import shutil
    import sys

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    shutil.rmtree(output_path, ignore_errors=True)
    os.makedirs(output_path)

    forks = Hardfork.discover()

    index_path = os.path.join(output_path, "index.rst")

    with open(index_path, "w") as f:
        f.write("===========\n")
        f.write("Comparisons\n")
        f.write("===========\n\n")

        f.write(".. toctree::\n")
        f.write("   :maxdepth: 1\n\n")

    for o, n in window(forks):
        diff(output_path, input_path, o, n)
