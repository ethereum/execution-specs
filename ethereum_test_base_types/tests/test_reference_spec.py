"""Test suite for `ethereum_test_base_types.reference_spec` module."""

import re

import pytest
import requests

from ..reference_spec.git_reference_spec import GitReferenceSpec
from ..reference_spec.reference_spec import NoLatestKnownVersionError

# the content field from https://api.github.com/repos/ethereum/EIPs/contents/EIPS/eip-100.md
# as of 2023-08-29
response_content = "LS0tCmVpcDogMTAwCnRpdGxlOiBDaGFuZ2UgZGlmZmljdWx0eSBhZGp1c3Rt\
ZW50IHRvIHRhcmdldCBtZWFuIGJsb2NrIHRpbWUgaW5jbHVkaW5nIHVuY2xl\
cwphdXRob3I6IFZpdGFsaWsgQnV0ZXJpbiAoQHZidXRlcmluKQp0eXBlOiBT\
dGFuZGFyZHMgVHJhY2sKY2F0ZWdvcnk6IENvcmUKc3RhdHVzOiBGaW5hbApj\
cmVhdGVkOiAyMDE2LTA0LTI4Ci0tLQoKIyMjIFNwZWNpZmljYXRpb24KCkN1\
cnJlbnRseSwgdGhlIGZvcm11bGEgdG8gY29tcHV0ZSB0aGUgZGlmZmljdWx0\
eSBvZiBhIGJsb2NrIGluY2x1ZGVzIHRoZSBmb2xsb3dpbmcgbG9naWM6Cgpg\
YGAgcHl0aG9uCmFkal9mYWN0b3IgPSBtYXgoMSAtICgodGltZXN0YW1wIC0g\
cGFyZW50LnRpbWVzdGFtcCkgLy8gMTApLCAtOTkpCmNoaWxkX2RpZmYgPSBp\
bnQobWF4KHBhcmVudC5kaWZmaWN1bHR5ICsgKHBhcmVudC5kaWZmaWN1bHR5\
IC8vIEJMT0NLX0RJRkZfRkFDVE9SKSAqIGFkal9mYWN0b3IsIG1pbihwYXJl\
bnQuZGlmZmljdWx0eSwgTUlOX0RJRkYpKSkKLi4uCmBgYAoKSWYgYGJsb2Nr\
Lm51bWJlciA+PSBCWVpBTlRJVU1fRk9SS19CTEtOVU1gLCB3ZSBjaGFuZ2Ug\
dGhlIGZpcnN0IGxpbmUgdG8gdGhlIGZvbGxvd2luZzoKCmBgYCBweXRob24K\
YWRqX2ZhY3RvciA9IG1heCgoMiBpZiBsZW4ocGFyZW50LnVuY2xlcykgZWxz\
ZSAxKSAtICgodGltZXN0YW1wIC0gcGFyZW50LnRpbWVzdGFtcCkgLy8gOSks\
IC05OSkKYGBgCiMjIyBSYXRpb25hbGUKClRoaXMgbmV3IGZvcm11bGEgZW5z\
dXJlcyB0aGF0IHRoZSBkaWZmaWN1bHR5IGFkanVzdG1lbnQgYWxnb3JpdGht\
IHRhcmdldHMgYSBjb25zdGFudCBhdmVyYWdlIHJhdGUgb2YgYmxvY2tzIHBy\
b2R1Y2VkIGluY2x1ZGluZyB1bmNsZXMsIGFuZCBzbyBlbnN1cmVzIGEgaGln\
aGx5IHByZWRpY3RhYmxlIGlzc3VhbmNlIHJhdGUgdGhhdCBjYW5ub3QgYmUg\
bWFuaXB1bGF0ZWQgdXB3YXJkIGJ5IG1hbmlwdWxhdGluZyB0aGUgdW5jbGUg\
cmF0ZS4gQSBmb3JtdWxhIHRoYXQgYWNjb3VudHMgZm9yIHRoZSBleGFjdCBu\
dW1iZXIgb2YgaW5jbHVkZWQgdW5jbGVzOgpgYGAgcHl0aG9uCmFkal9mYWN0\
b3IgPSBtYXgoMSArIGxlbihwYXJlbnQudW5jbGVzKSAtICgodGltZXN0YW1w\
IC0gcGFyZW50LnRpbWVzdGFtcCkgLy8gOSksIC05OSkKYGBgCmNhbiBiZSBm\
YWlybHkgZWFzaWx5IHNlZW4gdG8gYmUgKHRvIHdpdGhpbiBhIHRvbGVyYW5j\
ZSBvZiB+My80MTk0MzA0KSBtYXRoZW1hdGljYWxseSBlcXVpdmFsZW50IHRv\
IGFzc3VtaW5nIHRoYXQgYSBibG9jayB3aXRoIGBrYCB1bmNsZXMgaXMgZXF1\
aXZhbGVudCB0byBhIHNlcXVlbmNlIG9mIGBrKzFgIGJsb2NrcyB0aGF0IGFs\
bCBhcHBlYXIgd2l0aCB0aGUgZXhhY3Qgc2FtZSB0aW1lc3RhbXAsIGFuZCB0\
aGlzIGlzIGxpa2VseSB0aGUgc2ltcGxlc3QgcG9zc2libGUgd2F5IHRvIGFj\
Y29tcGxpc2ggdGhlIGRlc2lyZWQgZWZmZWN0LiBCdXQgc2luY2UgdGhlIGV4\
YWN0IGZvcm11bGEgZGVwZW5kcyBvbiB0aGUgZnVsbCBibG9jayBhbmQgbm90\
IGp1c3QgdGhlIGhlYWRlciwgd2UgYXJlIGluc3RlYWQgdXNpbmcgYW4gYXBw\
cm94aW1hdGUgZm9ybXVsYSB0aGF0IGFjY29tcGxpc2hlcyBhbG1vc3QgdGhl\
IHNhbWUgZWZmZWN0IGJ1dCBoYXMgdGhlIGJlbmVmaXQgdGhhdCBpdCBkZXBl\
bmRzIG9ubHkgb24gdGhlIGJsb2NrIGhlYWRlciAoYXMgeW91IGNhbiBjaGVj\
ayB0aGUgdW5jbGUgaGFzaCBhZ2FpbnN0IHRoZSBibGFuayBoYXNoKS4KCkNo\
YW5naW5nIHRoZSBkZW5vbWluYXRvciBmcm9tIDEwIHRvIDkgZW5zdXJlcyB0\
aGF0IHRoZSBibG9jayB0aW1lIHJlbWFpbnMgcm91Z2hseSB0aGUgc2FtZSAo\
aW4gZmFjdCwgaXQgc2hvdWxkIGRlY3JlYXNlIGJ5IH4zJSBnaXZlbiB0aGUg\
Y3VycmVudCB1bmNsZSByYXRlIG9mIDclKS4KCiMjIyBSZWZlcmVuY2VzCgox\
LiBFSVAgMTAwIGlzc3VlIGFuZCBkaXNjdXNzaW9uOiBodHRwczovL2dpdGh1\
Yi5jb20vZXRoZXJldW0vRUlQcy9pc3N1ZXMvMTAwCjIuIGh0dHBzOi8vYml0\
c2xvZy53b3JkcHJlc3MuY29tLzIwMTYvMDQvMjgvdW5jbGUtbWluaW5nLWFu\
LWV0aGVyZXVtLWNvbnNlbnN1cy1wcm90b2NvbC1mbGF3Lwo="


def test_git_reference_spec(monkeypatch):
    """Test Git reference spec."""

    def mock_get(self):
        class Response:
            content = (
                '{"content": "'
                + response_content
                + '", "sha":"78b94002190eb71cb04b8757629397f9418e8cce"}'
            )
            status_code = 200

        return Response()

    monkeypatch.setattr(requests, "get", mock_get)

    ref_spec = GitReferenceSpec(
        SpecPath="EIPS/eip-100.md",
    )

    latest_spec = ref_spec._get_latest_spec()
    assert latest_spec is not None
    assert "sha" in latest_spec
    assert re.match(r"^[0-9a-f]{40}$", latest_spec["sha"])
    with pytest.raises(NoLatestKnownVersionError):
        # `is_outdated` method raises here because known version is unset
        ref_spec.is_outdated()
    ref_spec.SpecVersion = "0000000000000000000000000000000000000000"
    assert ref_spec.is_outdated()
