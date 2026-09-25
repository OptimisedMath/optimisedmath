"""Shared reader for a rendered figure's printed labels (#352)."""

from xml.etree import ElementTree

_SVG_TEXT_TAG = "{http://www.w3.org/2000/svg}text"


def figure_labels(svg: str) -> list[str]:
    """Every label a rendered figure prints, as text, in document order.

    Parses with the standard-library XML parser rather than a regex, and
    never coerces a label to a number — a decimal label such as `42,54`
    must fail an assertion, not this helper's own parse.
    """
    root = ElementTree.fromstring(svg)
    return [element.text or "" for element in root.iter(_SVG_TEXT_TAG)]
