#!/usr/bin/env python3
import argparse
import os
import shutil
import tarfile

import requests


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
    geth_tar.extractall(dir)

    shutil.move(f"{dir}/{geth_release_name}/geth", dir)
    shutil.rmtree(f"{dir}/{geth_release_name}", ignore_errors=True)
    os.remove(f"{dir}/geth.tar.gz")


if __name__ == "__main__":
    args = parse_args()
    download_geth_linux(args.dir)
