import json


def change_endian(hex_string):
    return "0x" + hex_string[2:].zfill(64)[::-1]


def main(path, filename, toggle_endian=True):
    with open(path + filename) as file:
        data = json.load(file)

    for item in data[1:]:
        input_data = item["input"]
        y = input_data["y"]
        z = input_data["z"]

        if toggle_endian:
            input_data["y"] = change_endian(y)
            input_data["z"] = change_endian(z)
        else:
            input_data["y"] = change_endian(input_data["y"])
            input_data["z"] = change_endian(input_data["z"])

    with open(path + filename, "w") as file:
        json.dump(data, file, indent=2)


main(
    "fillers/eips/eip4844/point_evaluation_vectors/",
    "go_kzg_4844_verify_kzg_proof.json",
    toggle_endian=True,
)
