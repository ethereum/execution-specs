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
from logger import setup_logger
import os
import time

import ethereum_test_forks
from ethereum_test_tools import JSONEncoder, ReferenceSpec, ReferenceSpecTypes
from evm_block_builder import EvmBlockBuilder
from evm_transition_tool import EvmTransitionTool

from .modules import find_modules, is_module_modified


class Filler:
    """
    A command line tool to process test fillers into full hydrated tests.
    """

    log = setup_logger(__name__)

    def __init__(self, options: argparse.Namespace) -> None:
        self.options = options

    def fill(self) -> None:
        """
        Fill test fixtures.
        """
        if self.options.benchmark:
            start_time = time.time()

        if self.options.latest_fork:
            ethereum_test_forks.set_latest_fork_by_name(
                self.options.latest_fork
            )

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
            self.log.info(f"searching {module_full_name} for fillers")
            module = module_loader.load_module()
            module_dict = module.__dict__
            module_spec: ReferenceSpec | None = None
            has_reference_spec = False
            for ref_spec_type in ReferenceSpecTypes:
                if ref_spec_type.parseable_from_module(module_dict):
                    spec_obj = ref_spec_type.parse_from_module(module_dict)
                    if not spec_obj.has_known_version():
                        latest_version = spec_obj.latest_version()
                        self.log.warn(
                            f"""
                            Filler {spec_obj.name()} has a spec configuration,
                            but no latest known version.
                            Current version hash is: {latest_version}
                            If this is a new test, and you are using the latest
                            version, please include this value in the filler
                            .py file as:
                            `REFERENCE_SPEC_VERSION = "{latest_version}"`
                            """
                        )
                    else:
                        module_spec = spec_obj
                        try:
                            if module_spec.is_outdated():
                                latest_version = spec_obj.latest_version()
                                self.log.warn(
                                    f"""
                                    There is newer version of the spec
                                    referenced in filler {module_full_name},
                                    tests might be outdated:
                                    Spec: {module_spec.name()}
                                    Referenced version:
                                    {module_spec.known_version()}
                                    Latest version:
                                    {latest_version}
                                    """
                                )
                        except Exception as e:
                            self.log.warn(
                                f"""Unable to check latest version of spec
                                {module_spec.name()}: {e}"""
                            )
                    has_reference_spec = True
                    break

            ref_spec_ignore = module_full_name.split(".")[0] in [
                "vm",
                "example",
                "security",
            ]
            if not has_reference_spec and not ref_spec_ignore:
                self.log.warn(
                    f"""
                    Filler {module_full_name} has no reference spec information
                    """
                )
            for obj in module_dict.values():
                if callable(obj) and hasattr(obj, "__filler_metadata__"):
                    if (
                        self.options.test_case
                        and self.options.test_case
                        not in obj.__filler_metadata__["name"]
                    ):
                        continue
                    if len(obj.__filler_metadata__["forks"]) == 0:
                        continue
                    obj.__filler_metadata__["module_path"] = [
                        package_name.replace(".", "/"),
                        module_name,
                    ]
                    obj.__filler_metadata__["spec"] = module_spec
                    fillers.append(obj)
        return fillers

    def fill_fixture(self, filler, t8n, b11r):
        """
        Fills the specified fixture using the given filler,
        transaction tool, and block builder.
        """
        name = filler.__filler_metadata__["name"]
        module_path = filler.__filler_metadata__["module_path"]
        module_spec = filler.__filler_metadata__["spec"]
        output_dir = os.path.join(
            self.options.output,
            *(module_path if not self.options.no_output_structure else ""),
        )
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{name}.json")
        full_name = "/".join(module_path + [name])

        # Only skip if the fixture file already exists, the module
        # has not been modified since the last test filler run, and
        # the user doesn't want to force a refill the
        # fixtures (--force-refill).

        if (
            os.path.exists(path)
            and not is_module_modified(
                path, self.options.filler_path, module_path
            )
            and not self.options.force_refill
        ):
            self.log.info(f"skipping - {full_name}")
            return

        fixture = filler(t8n, b11r, "NoProof", module_spec)
        if fixture is not None:
            self.log.info(f"filled - {full_name}")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    fixture, f, ensure_ascii=False, indent=4, cls=JSONEncoder
                )
        else:
            self.log.info(f"skipping - {full_name}")
