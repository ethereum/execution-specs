#!/usr/bin/env python3
import argparse
import os
import shutil
import tarfile
import requests
from os.path import abspath
from os.path import dirname
from os.path import join as joinpath
from os.path import realpath

def _badpath(path, base):
    """Determines if a given file path is under a given base path or not.
    :param str path: file path where the file will be extracted to.
    :param str base: path to the current working directory.
    :return: False, if the path is under the given base, else True.
    :rtype: bool
    """
    # joinpath will ignore base if path is absolute
    return not realpath(abspath(joinpath(base, path))).startswith(base)


def _badlink(info, base):
    """Determine if a given link is under a given base path or not.
    :param TarInfo info: file that is going to be extracted.
    :param str base: path to the current working directory.
    :return: False, if the path is under the given base, else True.
    :rtype: bool
    """
    # Links are interpreted relative to the directory containing the link
    tip = realpath(abspath(joinpath(base, dirname(info.name))))
    return _badpath(info.linkname, base=tip)


def get_safe_members_in_tar_file(tarfile):
    """Retrieve members of a tar file that are safe to extract.
    :param Tarfile tarfile: the archive that has been opened as a TarFile
        object.
    :return: list of members in the archive that are safe to extract.
    :rtype: list
    """
    base = realpath(abspath(('.')))
    result = []
    for finfo in tarfile.getmembers():
        if _badpath(finfo.name, base):
            print(finfo.name + ' is blocked: illegal path.')
        elif finfo.issym() and _badlink(finfo, base):
            print(finfo.name + ' is blocked: Symlink to ' + finfo.linkname)
        elif finfo.islnk() and _badlink(finfo, base):
            print(finfo.name + ' is blocked: Hard link to ' + finfo.linkname)
        else:
            result.append(finfo)
    return result


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir", help="Directory to which geth binary will be downloaded to"
    )

    return parser.parse_args()


def download_geth_linux(dir: str) -> None:
    geth_release_name = "geth-linux-amd64-1.10.8-26675454"
    url = (
        f"https://gethstore.blob.core.windows.net/builds/"
        f"{geth_release_name}.tar.gz"
    )
    r = requests.get(url)

    with open(f"{dir}/geth.tar.gz", "wb") as f:
        f.write(r.content)

    geth_tar = tarfile.open(f"{dir}/geth.tar.gz")
    geth_tar.extractall(path=dir,
                        members=get_safe_members_in_tar_file(geth_tar))
        
    shutil.move(f"{dir}/{geth_release_name}/geth", dir)
    shutil.rmtree(f"{dir}/{geth_release_name}", ignore_errors=True)
    os.remove(f"{dir}/geth.tar.gz")


if __name__ == "__main__":
    args = parse_args()
    download_geth_linux(args.dir)
