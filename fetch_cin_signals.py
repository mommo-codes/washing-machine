import os
import sys
import json
import base64
import requests
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from typing import Optional

# =========================================================
# CONFIG
# =========================================================

BASE_URL = "https://services.validoo.se/tradeitem.api"
TOKEN_URL = "https://identity.validoo.se/connect/token"

load_dotenv()

CLIENT_ID = os.getenv("VALI_CLIENT_ID")
CLIENT_SECRET = os.getenv("VALI_CLIENT_SECRET")
USERNAME = os.getenv("VALI_USERNAME")
PASSWORD = os.getenv("VALI_PASSWORD")

if not all([CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD]):
    print("❌ Missing Validoo credentials in .env")
    sys.exit(1)

# =========================================================
# AUTH
# =========================================================


def get_access_token() -> str:
    payload = {
        "grant_type": "password",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "username": USERNAME,
        "password": PASSWORD,
        "scope": "tradeitem.api",
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(TOKEN_URL, data=payload, headers=headers)

    if resp.status_code != 200:
        raise RuntimeError(f"Token request failed: {resp.text}")

    return resp.json()["access_token"]


# =========================================================
# SEARCH + FETCH
# =========================================================


def search_by_gtin(token: str, gtin: str) -> list[dict]:
    url = f"{BASE_URL}/TradeItemInformation/search"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    payload = {"gtins": [gtin], "itemStatus": ["published"]}
    resp = requests.post(url, headers=headers, json=payload)

    if resp.status_code != 200:
        raise RuntimeError(f"Search failed: {resp.text}")

    return resp.json().get("results", [])


def get_item_by_id(token: str, item_id: int) -> dict:
    url = f"{BASE_URL}/TradeItemInformation/getItemById"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    params = {"id": item_id, "dataType": "Product", "allowInvalid": True}

    resp = requests.get(url, headers=headers, params=params)

    if resp.status_code != 200:
        raise RuntimeError(f"GetItemById failed: {resp.text}")

    return resp.json()[0]


# =========================================================
# CIN DECODING
# =========================================================


def decode_cin(cin_b64: Optional[str]) -> Optional[str]:
    if not cin_b64:
        return None
    return base64.b64decode(cin_b64).decode("utf-8")


# =========================================================
# CIN SIGNAL EXTRACTION
# =========================================================


NS = {
    "cin": "urn:gs1:gdsn:catalogue_item_notification:xsd:3",
}


def _text(root, path):
    el = root.find(path, NS)
    return el.text.strip() if el is not None and el.text else None


def extract_cin_signals(cin_xml: str) -> dict:
    root = ET.fromstring(cin_xml)

    signals = {
        # Identity
        "gtin": _text(root, ".//gtin"),
        "supplier_gln": _text(root, ".//informationProviderOfTradeItem/gln"),
        "supplier_name": _text(root, ".//informationProviderOfTradeItem/partyName"),
        # Classification
        "gpc_code": _text(root, ".//gpcCategoryCode"),
        "gpc_name": _text(root, ".//gpcCategoryName"),
        # Market
        "target_market_country_code": _text(root, ".//targetMarketCountryCode"),
        # Naming
        "brand_name": _text(root, ".//brandName"),
        "functional_name_sv": _text(root, ".//functionalName[@languageCode='sv']"),
        "description_short_sv": _text(root, ".//descriptionShort[@languageCode='sv']"),
        # VAT
        "vat_rate": _text(root, ".//dutyFeeTaxRate"),
        # Trade unit flags
        "is_consumer_unit": _text(root, ".//isTradeItemAConsumerUnit"),
        "is_base_unit": _text(root, ".//isTradeItemABaseUnit"),
        "is_variable_unit": _text(root, ".//isTradeItemAVariableUnit"),
        # Size / quantity
        "descriptive_size_sv": _text(
            root, ".//descriptiveSizeDimension[@languageCode='sv']"
        ),
        "net_content": _text(root, ".//netContent"),
        "net_content_unit": (
            _text(root, ".//netContent").strip()
            if _text(root, ".//netContent")
            else None
        ),
        # Physical dimensions
        "width_mm": _text(root, ".//width"),
        "height_mm": _text(root, ".//height"),
        "depth_mm": _text(root, ".//depth"),
        "gross_weight_g": _text(root, ".//grossWeight"),
        # Packaging
        "packaging_type": _text(root, ".//packagingTypeCode"),
        "packaging_material": _text(root, ".//packagingMaterialTypeCode"),
        "is_returnable": _text(root, ".//isPackagingMarkedReturnable"),
        # Dates
        "first_available_consumer": _text(root, ".//consumerFirstAvailabilityDateTime"),
        "start_availability": _text(root, ".//startAvailabilityDateTime"),
        "last_change": _text(root, ".//lastChangeDateTime"),
        "effective_date": _text(root, ".//effectiveDateTime"),
    }

    return signals


# =========================================================
# MAIN
# =========================================================


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 fetch_cin_signals.py <GTIN>")
        sys.exit(1)

    gtin = sys.argv[1]

    print(f"🔎 Fetching GTIN {gtin}")
    token = get_access_token()

    results = search_by_gtin(token, gtin)
    matches = [r for r in results if r.get("gtin") == gtin]

    if not matches:
        print("❌ GTIN not found")
        sys.exit(1)

    consumer_units = [r for r in matches if r.get("isTradeItemAConsumerUnit") is True]

    item_id = (
        consumer_units[0]["itemId"]
        if len(consumer_units) == 1
        else matches[0]["itemId"]
    )

    item = get_item_by_id(token, item_id)

    with open("trade_item_raw.json", "w", encoding="utf-8") as f:
        json.dump(item, f, indent=2, ensure_ascii=False)

    cin_xml = decode_cin(item.get("cin"))

    if not cin_xml:
        print("⚠️ No CIN available")
        sys.exit(0)

    with open("cin.xml", "w", encoding="utf-8") as f:
        f.write(cin_xml)

    signals = extract_cin_signals(cin_xml)

    with open("cin_signals.json", "w", encoding="utf-8") as f:
        json.dump(signals, f, indent=2, ensure_ascii=False)

    print("✅ Done")
    print("📁 trade_item_raw.json")
    print("📁 cin.xml")
    print("📁 cin_signals.json")


if __name__ == "__main__":
    main()
