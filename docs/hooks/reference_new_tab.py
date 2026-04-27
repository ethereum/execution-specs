"""
Add `target="_blank"` to links pointing at the `docc`-rendered reference.

Without this, Material's `navigation.instant` intercepts clicks and tries to
XHR-swap the target page into the current DOM, which fails silently because
`docc`'s HTML does not match Material's template markers: the URL and title
update but the body stays on the original page. `target="_blank"` makes
instant-nav opt out and forces a full-page load, matching the home page card
that already sets the attribute via `attr_list`.

Matches every relative href form mkdocs emits for the reference page across
page depths (e.g., `reference/`, `../reference/`, `specs/reference/`,
`../../specs/reference/`). The trailing slash after `reference` prevents
matching unrelated paths like `reference_specification/`.
"""

import re

_A_TAG_REF = re.compile(
    r'<a\s+([^>]*?href="(?:\.\./)*(?:specs/)?reference/(?:index\.html)?"[^>]*?)>'
)


def _rewrite(match: "re.Match[str]") -> str:
    attrs = match.group(1)
    if "target=" in attrs:
        return match.group(0)
    return f'<a {attrs} target="_blank" rel="noopener">'


def on_post_page(output: str, page, config) -> str:
    """Rewrite anchor tags pointing at the reference to open in a new tab."""
    del page, config
    return _A_TAG_REF.sub(_rewrite, output)
