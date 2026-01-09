import xml.etree.ElementTree as ET
from typing import Any, Dict, Union
import sys
import json
import re


# -------------------------------------------------
# Utils
# -------------------------------------------------

URL_RE = re.compile(r"https?://", re.IGNORECASE)


def strip_namespace(tag: str) -> str:
    """Remove XML namespace from tag."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def is_url(text: str) -> bool:
    return bool(URL_RE.search(text))


# -------------------------------------------------
# Core XML → dict conversion
# -------------------------------------------------


def element_to_dict(el: ET.Element) -> Union[Dict[str, Any], str]:
    """
    Convert XML element to ordered dict-like structure.
    Preserves:
    - attributes
    - children order
    - repeated elements as lists
    """

    node: Dict[str, Any] = {}

    # Attributes
    if el.attrib:
        node["@attributes"] = dict(el.attrib)

    # Children
    children = list(el)
    if children:
        for child in children:
            tag = strip_namespace(child.tag)
            value = element_to_dict(child)

            if tag in node:
                # Turn into list if repeated
                if not isinstance(node[tag], list):
                    node[tag] = [node[tag]]
                node[tag].append(value)
            else:
                node[tag] = value
    else:
        # Leaf node
        text = el.text.strip() if el.text else ""
        if text:
            # Strip URLs but keep key
            if is_url(text):
                return None
            return text
        return None

    return node


# -------------------------------------------------
# Public API
# -------------------------------------------------


def extract_cin_raw(cin_xml: str) -> Dict[str, Any]:
    root = ET.fromstring(cin_xml)
    return {strip_namespace(root.tag): element_to_dict(root)}


# -------------------------------------------------
# CLI entrypoint
# -------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 cin_raw_extractor.py <cin.xml> <out.json>")
        sys.exit(1)

    xml_path = sys.argv[1]
    out_path = sys.argv[2]

    with open(xml_path, "r", encoding="utf-8") as f:
        cin_xml = f.read()

    data = extract_cin_raw(cin_xml)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ CIN snapshot written to {out_path}")
