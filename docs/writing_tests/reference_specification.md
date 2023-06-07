# Referencing an EIP Spec Version

An Ethereum Improvement Proposal (from [ethereum/EIPs](https://github.com/ethereum/EIPs/tree/master/EIPS)) and its SHA digest can be directly referenced within a python test module in order to check whether the test implementation could be out-dated. If the SHA of the file in the remote repo changes, the test framework will issue a warning in its summary section.

Test cases located underneath `./fillers/eips/` _must_ define a reference spec version.

<figure markdown>
 ![Examples of warnings in the test framework's console output when an EIP is outdated or not specified](./img/reference_spec_warning_console_output.png){ width=auto align=center}
</figure>

!!! info ""
    The SHA value is the output from git's `hash-object` command, for example:
    ```console
    git clone git@github.com:ethereum/EIPs
    git hash-object EIPS/EIPS/eip-3651.md
    # output: d94c694c6f12291bb6626669c3e8587eef3adff1
    ```
    and can be retrieved from the remote repo via the Github API on the command-line as following:
    ```console
    sudo apt install jq
    curl -s -H "Accept: application/vnd.github.v3+json" \
    https://api.github.com/repos/ethereum/EIPs/contents/EIPS/eip-3651.md |\
    jq -r '.sha'
    # output: d94c694c6f12291bb6626669c3e8587eef3adff1
    ```

## How to Add a Spec Version Check

This check accomplished by adding the following two global variables anywhere in the Python source file:

| Variable Name               | Explanation                                                                                                                                                        |
|-----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `REFERENCE_SPEC_GIT_PATH`   | The relative path of the EIP markdown file in the [ethereum/EIPs](https://github.com/ethereum/EIPs/) repository, e.g. "`EIPS/eip-1234.md`"                         |
| `REFERENCE_SPEC_VERSION`    | The SHA hash of the latest version of the file retrieved from the Github API:<br>`https://api.github.com/repos/ethereum/EIPs/contents/EIPS/eip-<EIP Number>.md` |

## Example

Here is an example from [./fillers/eips/test_eip3651.py](../fillers/EIPs/eip3651.md):

```python
REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3651.md"
REFERENCE_SPEC_VERSION = "d94c694c6f12291bb6626669c3e8587eef3adff1"
```
The SHA digest was retrieved [from here](https://api.github.com/repos/ethereum/EIPs/contents/EIPS/eip-3651.md).