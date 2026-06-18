"""Helper to load predeploy contract bytecode bundled as package data."""

import pkgutil


def load_contract_bytecode(module_name: str, filename: str) -> bytes:
    """
    Load predeploy contract bytecode bundled as package data.

    `module_name` is the importing module's `__name__`; the bytecode is read
    from a `contracts/<filename>` resource located alongside that module.
    """
    resource = f"contracts/{filename}"
    bytecode = pkgutil.get_data(module_name, resource)
    if bytecode is None:
        raise FileNotFoundError(
            f"Unable to read bytecode `{resource}` from `{module_name}`"
        )
    return bytecode
