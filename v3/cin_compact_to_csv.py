#!/usr/bin/env python3
import json
import csv
from pathlib import Path

IN_PATH = Path("cin_compact.json")
OUT_PATH = Path("cin_compact_wide.csv")


def first_text(items, lang="sv"):
    for i in items:
        if i.get("lang") == lang:
            return i.get("text")
    return None


with IN_PATH.open(encoding="utf-8") as f:
    d = json.load(f)


row = {
    # -------------------------------------------------
    # Identity
    # -------------------------------------------------
    "gtin": d["identity"]["gtin"],
    "brand": d["identity"]["brand"],
    "supplier_assigned_id": d["identity"]["supplier_assigned_id"],
    "gpc_code": d["classification"]["gpc_code"],
    "gpc_name": d["classification"]["gpc_name"],
    "target_country": d["market"]["target_country_code"],
    "country_of_origin": d["market"]["country_of_origin"],
    # -------------------------------------------------
    # Naming (SV)
    # -------------------------------------------------
    "description_short_sv": first_text(d["naming"]["description_short"]),
    "functional_name_sv": first_text(d["naming"]["functional_name"]),
    "regulated_product_name_sv": first_text(d["naming"]["regulated_product_name"]),
    # -------------------------------------------------
    # Size & measurements
    # -------------------------------------------------
    "size_descriptive": d["size"]["descriptive"],
    "net_content": d["size"]["net_content"],
    "width_mm": d["measurements"]["width_mm"],
    "height_mm": d["measurements"]["height_mm"],
    "depth_mm": d["measurements"]["depth_mm"],
    "gross_weight_g": d["measurements"]["gross_weight_g"],
    # -------------------------------------------------
    # Commercial
    # -------------------------------------------------
    "vat_rate": d["vat"]["rate"],
    # -------------------------------------------------
    # Legal / regulatory (RAW)
    # -------------------------------------------------
    "sales_condition_code": d["sales_restrictions"]["condition_code"],
    "minimum_age": d["consumer_guidance"]["minimum_age"],
    "is_otc": d["healthcare"]["is_otc"],
    "alcohol_abv": d["alcohol"]["abv_percent"],
    # -------------------------------------------------
    # Ingredients & allergens
    # -------------------------------------------------
    "ingredients_sv": first_text(d["ingredients"]["food"]),
    "allergens": " | ".join(f"{a['type']}({a['containment']})" for a in d["allergens"]),
    # -------------------------------------------------
    # Marketing
    # -------------------------------------------------
    "marketing_text_sv": first_text(d["marketing"]["long"]),
    "keywords_sv": first_text(d["marketing"]["keywords"]),
    # -------------------------------------------------
    # Media
    # -------------------------------------------------
    "primary_image": next((m["uri"] for m in d["media"] if m["primary"]), None),
    "all_image_urls": " | ".join(
        m["uri"] for m in d["media"] if m["type"] == "PRODUCT_IMAGE"
    ),
}


with OUT_PATH.open("w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=row.keys())
    writer.writeheader()
    writer.writerow(row)

print("✅ cin_compact_wide.csv written")
