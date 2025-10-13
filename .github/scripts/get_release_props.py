# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "pyyaml",
#     "click",
# ]
# ///
"""Extract the properties of a configured EEST release from a YAML file."""

import sys

import click
import yaml

RELEASE_PROPS_FILE = "./.github/configs/feature.yaml"


@click.command()
@click.argument("release", required=True)
def get_release_props(release: str) -> None:
    """Extract the properties from the YAML file for a given release."""
    with open(RELEASE_PROPS_FILE) as f:
        data = yaml.safe_load(f)
    if release not in data:
        print(f"Error: Release {release} not found in {RELEASE_PROPS_FILE}.")
        sys.exit(1)
    print("\n".join(f"{key}={value}" for key, value in data[release].items()))


if __name__ == "__main__":
    get_release_props()
