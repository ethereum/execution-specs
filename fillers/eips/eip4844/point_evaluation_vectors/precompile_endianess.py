# FOR BIG ENDIAN Z/Y:
# `python precompile_endianess big`
# FOR LITTLE ENDIAN Z/Y:
# `python precompile_endianess little`

import json
import sys


def set_endian(hex_string, current_endianess, target_endianess):
    bytes_list = [hex_string[i : i + 2] for i in range(2, len(hex_string), 2)]
    if current_endianess != target_endianess:
        return "0x" + "".join(reversed(bytes_list))
    else:
        return hex_string


def main(path, filename, target_endianess="little"):
    with open(path + filename) as file:
        data = json.load(file)
    first_item = data[1]["input"]["z"]
    exp = "0x5eb7004fe57383e6c88b99d839937fddf3f99279353aaf8d5c9a75f91ce33c62"
    if first_item == exp:
        current_endianess = "big"
    else:
        current_endianess = "little"

    for item in data[1:]:
        input_data = item["input"]
        y = input_data["y"]
        z = input_data["z"]

        input_data["y"] = set_endian(y, current_endianess, target_endianess)
        input_data["z"] = set_endian(z, current_endianess, target_endianess)

    with open(path + filename, "w") as file:
        json.dump(data, file, indent=2)


# Command-line argument for endianess
target_endianess = sys.argv[1]

main(
    "fillers/eips/eip4844/point_evaluation_vectors/",
    "go_kzg_4844_verify_kzg_proof.json",
    target_endianess,
)
