import pathlib

import setuptools

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")

setuptools.setup(
    long_description=long_description,
    long_description_content_type="text/markdown",
)
