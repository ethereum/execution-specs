import xml.etree.ElementTree as ET
import json


def parse_coverage_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    result = {}

    for cls in root.findall(".//class"):
        filename = cls.attrib["filename"]
        lines = cls.find("lines")
        if lines is None:
            continue
        covered = []
        missing = []
        for line in lines.findall("line"):
            num = int(line.attrib["number"])
            hits = int(line.attrib["hits"])
            if hits > 0:
                covered.append(num)
            else:
                missing.append(num)
        result[filename] = {
            "covered_lines": covered,
            "missing_lines": missing
        }
    return result


if __name__ == "__main__":
    xml_path = ".tox/coverage.xml"
    out_file = "baseline_coverage.json"

    data = parse_coverage_xml(xml_path)
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {out_file}")
