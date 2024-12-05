"""
Helper methods used in the spec tests.
"""


def remove_info_metadata(fixture_json):  # noqa: D103
    for t in fixture_json:
        if "_info" in fixture_json[t]:
            info_keys = list(fixture_json[t]["_info"].keys())
            for key in info_keys:
                if key != "hash":  # remove keys that are not 'hash'
                    del fixture_json[t]["_info"][key]
