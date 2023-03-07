"""
Utility functions for finding and working with modules.

Functions:
    is_module_modified: Checks if a module was modified more
        recently than it was filled.
    find_modules: Recursively finds modules in a directory,
        filtered by package and module name.
    recursive_iter_modules: Iterates through all sub-packages
        of a package to find modules.
"""
import os
from pkgutil import iter_modules

from setuptools import find_packages


def is_module_modified(path, pkg_path, module_path):
    """
    Returns True if a module was modified more recently than
    it was filled, False otherwise.
    """
    modified_time = os.path.getmtime(
        os.path.join(pkg_path, *module_path) + ".py"
    )
    filled_time = os.path.getmtime(path) if os.path.exists(path) else 0
    return modified_time > filled_time


def find_modules(root, include_pkg, include_modules):
    """
    Find modules recursively starting with the `root`.
    Only modules in a package with name found in iterable `include_pkg` will be
    yielded.
    Only modules with name found in iterable `include_modules` will be yielded.
    """
    modules = set()
    for package in find_packages(
        root,
        include=include_pkg if include_pkg is not None else ("*",),
    ):
        package = package.replace(
            ".", "/"
        )  # sub_package tests i.e 'vm.vm_tests'
        for info, package_path in recursive_iter_modules(root, package):
            module_full_name = package_path + "." + info.name
            if module_full_name not in modules:
                if not include_modules or include_modules in info.name:
                    yield (
                        package,
                        info.name,
                        info.module_finder.find_module(module_full_name),
                    )
                modules.add(module_full_name)


def recursive_iter_modules(root, package):
    """
    Helper function for find_packages.
    Iterates through all sub-packages (packages within a package).
    Recursively navigates down the package tree until a new module is found.
    """
    for info in iter_modules([os.path.join(root, package)]):
        if info.ispkg:
            yield from recursive_iter_modules(
                root, os.path.join(package, info.name)
            )
        else:
            package_path = package.replace("/", ".")
            yield info, package_path
