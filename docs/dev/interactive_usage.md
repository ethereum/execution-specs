# Working with EEST Libraries Interactively

You can work with EEST Python packages interactively with `ipython` using:

```console
uvx  --with-editable . ipython
```

This command will create a virtual environment, install EEST's packages in "[editable mode](https://setuptools.pypa.io/en/latest/userguide/development_mode.html)" (source changes get reflected in the interactive shell), and start an `ipython` shell. You can then import any of the packages and experiment with them interactively.

!!! example "Example: Working with `ethereum_test_forks`"

    See which defined forks are "ignored" by default:

    ```python
    from ethereum_test_forks import forks, get_forks
    forks = set([fork for fork in get_forks() if fork.ignore()])
    print(forks)
    # -> {MuirGlacier, ArrowGlacier, GrayGlacier}
    ```

## Required `ipython` Configuration

To enable [autoreload](https://ipython.readthedocs.io/en/stable/config/extensions/autoreload.html) of changed modules in the current `ipython` session, type:

```python
%load_ext autoreload
%autoreload 2
```

To make this configuration persistent, add/uncomment the following lines to `~/.ipython/profile_default/ipython_config.py`:

```python
c.InteractiveShellApp.exec_lines = ["%autoreload 2"]
c.InteractiveShellApp.extensions = ["autoreload"]
```
