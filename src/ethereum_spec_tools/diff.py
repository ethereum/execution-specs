#!/usr/bin/env python3

"""
Generates diffs between Ethereum hardforks documentation.
"""

import os.path
import pickle
from copy import deepcopy
from typing import Any, Iterator, List, TypeVar

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


def find_pickles(path: str, fork: Hardfork) -> Iterator[str]:
    """
    Find files ending with :code:`.pickle`.
    """
    for directory, _, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith(".pickle"):
                file_path = os.path.join(directory, filename)
                file_path = file_path[len(path) + 1 :]
                yield file_path


def meaningful_diffs(
    pub: rstdiff.Publisher3Args,
    old: Any,
    new: Any,
) -> bool:
    """Find if there are meaningful differences between the docs"""
    realDebug = pub.settings.debug
    pub.settings.debug = pub.settings.dump_rstdiff
    reporter = new_reporter("RSTDIFF", pub.settings)
    pub.settings.debug = realDebug
    dispatcher = rstdiff.DocutilsDispatcher(reporter)
    opcodes = rstdiff.doDiff(dispatcher, old, new)

    opcode_counter = rstdiff.OpcodeCounter(opcodes)
    opcode_counter.count()

    if (
        opcode_counter.replace
        == opcode_counter.delete
        == opcode_counter.insert
        == 0
    ):
        return False
    else:
        return True


def diff(
    output_path: str, input_path: str, old: Hardfork, new: Hardfork
) -> Iterator[str]:
    """
    Calculate the structured diff between two hardforks.
    """
    trivial_changes = [
        (old.short_name, new.short_name),
        (old.title_case_name, new.title_case_name),
    ]

    old_path = old.name.replace(".", os.sep)
    old_path = os.path.join(input_path, old_path)

    new_path = new.name.replace(".", os.sep)
    new_path = os.path.join(input_path, new_path)

    diff_path = old.short_name + "_" + new.short_name
    diff_path = os.path.join(output_path, diff_path)

    old_pickles = set(find_pickles(old_path, old))
    new_pickles = set(find_pickles(new_path, new))

    pickles = old_pickles | new_pickles

    for count, pickle_path in enumerate(pickles, start=1):
        old_pickle_path = os.path.join(old_path, pickle_path)
        new_pickle_path = os.path.join(new_path, pickle_path)
        diff_pickle_path = os.path.join(diff_path, pickle_path + "64")

        diff_dir_path = os.path.dirname(diff_pickle_path)

        os.makedirs(diff_dir_path, exist_ok=True)

        try:
            with open(old_pickle_path, "rb") as old_file:
                old_doc = pickle.load(old_file)
        except FileNotFoundError:
            old_doc = new_document(old_pickle_path)
            old_pickle_path = os.devnull

        try:
            with open(new_pickle_path, "rb") as new_file:
                new_doc = pickle.load(new_file)
        except FileNotFoundError:
            new_doc = new_document(new_pickle_path)
            new_pickle_path = os.devnull

        print(
            f"[{count}/{len(pickles)}] diff",
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

        old_doc.settings = pub.settings
        old_doc.reporter = new_reporter("RSTDIFF", pub.settings)

        new_doc.settings = pub.settings
        new_doc.reporter = new_reporter("RSTDIFF", pub.settings)

        old_modified_doc = deepcopy(old_doc)
        old_modified_doc.settings = pub.settings
        old_modified_doc.reporter = new_reporter("RSTDIFF", pub.settings)

        rstdiff.TextReplacer(old_modified_doc, trivial_changes).apply()

        if not meaningful_diffs(pub, old_modified_doc, new_doc):
            continue

        rstdiff.Text2Words(old_doc).apply()
        rstdiff.Text2Words(new_doc).apply()

        try:
            diff_doc = rstdiff.createDiff(pub, old_doc, new_doc)
        except rstdiff.DocumentUnchanged:
            continue

        rstdiff.Words2Text(diff_doc).apply()
        rstdiff.Generated2Inline(diff_doc).apply()

        pub.writer.write(diff_doc, pub.destination)
        pub.writer.assemble_parts()

        yield os.path.abspath(diff_pickle_path)


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

    diffs = (diff(output_path, input_path, o, n) for o, n in window(forks))
    paths = (item for inner in diffs for item in inner)
    paths = (os.path.relpath(d, output_path) for d in paths)
    paths = (os.path.splitext(d)[0] for d in paths)

    index_path = os.path.join(output_path, "index.rst")

    with open(index_path, "w") as f:
        f.write("===========\n")
        f.write("Comparisons\n")
        f.write("===========\n\n")

        f.write(".. toctree::\n")
        f.write("   :maxdepth: 1\n\n")

        for item in paths:
            f.write(f"   {item}\n")
