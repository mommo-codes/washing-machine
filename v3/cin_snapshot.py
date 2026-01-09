# cin_snapshot.py
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Union


def xml_to_dict(el: ET.Element) -> Dict[str, Any]:
    """
    Convert an XML element into a JSON-serializable dict.
    Preserves:
    - tag names (with namespace)
    - attributes
    - children
    - text
    """

    node: Dict[str, Any] = {
        "tag": el.tag,
    }

    if el.attrib:
        node["attributes"] = dict(el.attrib)

    children = list(el)
    if children:
        node["children"] = [xml_to_dict(child) for child in children]

    text = (el.text or "").strip()
    if text:
        node["text"] = text

    return node


def snapshot_cin(cin_xml: str) -> Dict[str, Any]:
    root = ET.fromstring(cin_xml)
    return xml_to_dict(root)
