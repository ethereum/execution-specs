import setuptools

setuptools.setup(
    packages=setuptools.find_packages(
        where="src",
        exclude=("*.tests",),
    )
)
