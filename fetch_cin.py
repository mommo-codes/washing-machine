import os
import sys
import json
import base64
import requests
from dotenv import load_dotenv

from cin_extract import extract_cin_signals

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
        raise RuntimeError(resp.text)

    return resp.json()["access_token"]


# =========================================================
# VALI FETCH
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
        raise RuntimeError(resp.text)

    return resp.json().get("results", [])


def get_item_by_id(token: str, item_id: int) -> dict:
    url = f"{BASE_URL}/TradeItemInformation/getItemById"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    params = {"id": item_id, "dataType": "Product", "allowInvalid": True}

    resp = requests.get(url, headers=headers, params=params)

    if resp.status_code != 200:
        raise RuntimeError(resp.text)

    return resp.json()[0]


def decode_cin(cin_b64: str | None) -> str | None:
    if not cin_b64:
        return None
    return base64.b64decode(cin_b64).decode("utf-8")


# =========================================================
# MAIN
# =========================================================


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 fetch_cin.py <GTIN>")
        sys.exit(1)

    gtin = sys.argv[1]
    print(f"🔎 Fetching {gtin}")

    token = get_access_token()
    results = search_by_gtin(token, gtin)

    matches = [r for r in results if r.get("gtin") == gtin]
    if not matches:
        print("❌ GTIN not found")
        sys.exit(1)

    consumer_units = [r for r in matches if r.get("isTradeItemAConsumerUnit") is True]

    item_id = consumer_units[0]["itemId"] if consumer_units else matches[0]["itemId"]
    item = get_item_by_id(token, item_id)

    with open("trade_item_raw.json", "w", encoding="utf-8") as f:
        json.dump(item, f, indent=2, ensure_ascii=False)

    cin_xml = decode_cin(item.get("cin"))
    if not cin_xml:
        print("⚠️ No CIN returned")
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
