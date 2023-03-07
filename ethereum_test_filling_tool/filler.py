"""
Provides the Filler Class:

Fillers are python functions that, given an `EvmTransitionTool` and
`EvmBlockBuilder`, return a JSON object representing an Ethereum test case.

This tool will traverse a package of filler python modules, fill each test
case within it, and write them to a file in a given output directory.
"""
import argparse
import concurrent.futures
import json
import logging
import os
import time

from ethereum_test_tools import JSONEncoder
from evm_block_builder import EvmBlockBuilder
from evm_transition_tool import EvmTransitionTool

from .modules import find_modules, is_module_modified


class Filler:
    """
    A command line tool to process test fillers into full hydrated tests.
    """

    log: logging.Logger

    def __init__(self, options: argparse.Namespace) -> None:
        self.log = logging.getLogger(__name__)
        self.options = options

    def fill(self) -> None:
        """
        Fill test fixtures.
        """
        if self.options.benchmark:
            start_time = time.time()

        fillers = self.get_fillers()
        self.log.info(f"collected {len(fillers)} fillers")

        os.makedirs(self.options.output, exist_ok=True)

        t8n = EvmTransitionTool(
            binary=self.options.evm_bin, trace=self.options.traces
        )
        b11r = EvmBlockBuilder(binary=self.options.evm_bin)

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.options.max_workers
        ) as executor:
            futures = []
            for filler in fillers:
                future = executor.submit(self.fill_fixture, filler, t8n, b11r)
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                future.result()

        if self.options.benchmark:
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.log.info(
                f"Filled test fixtures in {elapsed_time:.2f} seconds."
            )

    def get_fillers(self):
        """
        Returns a list of all fillers found in the specified package
        and modules.
        """
        fillers = []
        for package_name, module_name, module_loader in find_modules(
            os.path.abspath(self.options.filler_path),
            self.options.test_categories,
            self.options.test_module,
        ):
            module_full_name = module_loader.name
            self.log.debug(f"searching {module_full_name} for fillers")
            module = module_loader.load_module()
            for obj in module.__dict__.values():
                if callable(obj) and hasattr(obj, "__filler_metadata__"):
                    if (
                        self.options.test_case
                        and self.options.test_case
                        not in obj.__filler_metadata__["name"]
                    ):
                        continue
                    obj.__filler_metadata__["module_path"] = [
                        package_name,
                        module_name,
                    ]
                    fillers.append(obj)
        return fillers

    def fill_fixture(self, filler, t8n, b11r):
        """
        Fills the specified fixture using the given filler,
        transaction tool, and block builder.
        """
        name = filler.__filler_metadata__["name"]
        module_path = filler.__filler_metadata__["module_path"]
        output_dir = os.path.join(
            self.options.output,
            *(module_path if not self.options.no_output_structure else ""),
        )
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{name}.json")
        full_name = ".".join(module_path + [name])

        # Only skip if the fixture file already exists, the module
        # has not been modified since the last test filler run, and
        # the user does not want to overwrite the fixtures (--overwrite).
        if (
            os.path.exists(path)
            and not is_module_modified(
                path, self.options.filler_path, module_path
            )
            and not self.options.force_refill
        ):
            self.log.debug(f"skipping - {full_name}")
            return

        fixture = filler(t8n, b11r, "NoProof")
        self.log.debug(f"filling - {full_name}")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                fixture, f, ensure_ascii=False, indent=4, cls=JSONEncoder
            )
