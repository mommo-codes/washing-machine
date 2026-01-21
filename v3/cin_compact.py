#!/usr/bin/env python3
import json
from pathlib import Path

SNAPSHOT_PATH = Path("cin_snapshot.json")
OUT_PATH = Path("cin_compact.json")


# helpers
def find_all(node, tag_endswith):
    if not node:
        return []
    hits = []
    if node.get("tag", "").endswith(tag_endswith):
        hits.append(node)
    for c in node.get("children", []) or []:
        hits.extend(find_all(c, tag_endswith))
    return hits


def find_first(node, tag_endswith):
    hits = find_all(node, tag_endswith)
    return hits[0] if hits else None


def text(node):
    return node.get("text") if node else None


def attr(node, key):
    return node.get("attributes", {}).get(key) if node else None


with SNAPSHOT_PATH.open() as f:
    root = json.load(f)


colour_node = find_first(root, "colour")
size_node = find_first(root, "descriptiveSizeDimension")


compact = {
    "identity": {
        "gtin": text(find_first(root, "gtin")),
        "brand": text(find_first(root, "brandName")),
        "supplier_assigned_id": text(
            find_first(root, "additionalTradeItemIdentification")
        ),
        "trade_channel": text(find_first(root, "tradeItemTradeChannelCode")),
        "information_provider": {
            "gln": text(find_first(root, "informationProviderOfTradeItem/gln")),
            "name": text(find_first(root, "informationProviderOfTradeItem/partyName")),
            "address": text(
                find_first(root, "informationProviderOfTradeItem/partyAddress")
            ),
        },
        "manufacturer": {
            "gln": text(find_first(root, "manufacturerOfTradeItem/gln")),
            "name": text(find_first(root, "manufacturerOfTradeItem/partyName")),
        },
    },
    "classification": {
        "gpc_code": text(find_first(root, "gpcCategoryCode")),
        "gpc_name": text(find_first(root, "gpcCategoryName")),
    },
    "market": {
        "target_country_code": text(find_first(root, "targetMarketCountryCode")),
        "country_of_origin": text(find_first(root, "countryCode")),
    },
    "variant": {
        "supplier_assigned_id": text(
            find_first(root, "additionalTradeItemIdentification")
        ),
        "color": (
            {
                "code": text(find_first(colour_node, "colourCode")),
                "name": text(find_first(colour_node, "colourDescription")),
            }
            if colour_node
            else None
        ),
        "size": text(size_node),
        "net_content": text(find_first(root, "netContent")),
    },
    "naming": {
        "description_short": [
            {
                "lang": attr(n, "languageCode"),
                "text": text(n),
            }
            for n in find_all(root, "descriptionShort")
        ],
        "functional_name": [
            {
                "lang": attr(n, "languageCode"),
                "text": text(n),
            }
            for n in find_all(root, "functionalName")
        ],
        "regulated_product_name": [
            {
                "lang": attr(n, "languageCode"),
                "text": text(n),
            }
            for n in find_all(root, "regulatedProductName")
        ],
    },
    "vat": {
        "type": text(find_first(root, "dutyFeeTaxTypeCode")),
        "rate": text(find_first(root, "dutyFeeTaxRate")),
    },
    "trade_unit": {
        "is_consumer_unit": text(find_first(root, "isTradeItemAConsumerUnit"))
        == "true",
        "is_base_unit": text(find_first(root, "isTradeItemABaseUnit")) == "true",
        "is_variable_unit": text(find_first(root, "isTradeItemAVariableUnit"))
        == "true",
        "is_orderable_unit": text(find_first(root, "isTradeItemAnOrderableUnit"))
        == "true",
        "is_invoice_unit": text(find_first(root, "isTradeItemAnInvoiceUnit")) == "true",
    },
    "size": {
        "descriptive": text(find_first(root, "descriptiveSizeDimension")),
        "net_content": text(find_first(root, "netContent")),
    },
    "measurements": {
        "width_mm": text(find_first(root, "width")),
        "height_mm": text(find_first(root, "height")),
        "depth_mm": text(find_first(root, "depth")),
        "gross_weight_g": text(find_first(root, "grossWeight")),
        "net_weight_g": text(find_first(root, "netWeight")),
    },
    "alcohol": {
        "abv_percent": text(find_first(root, "percentageOfAlcoholByVolume")),
    },
    "healthcare": {
        "prescription_type": text(find_first(root, "prescriptionTypeCode")),
        "is_otc": text(find_first(root, "prescriptionTypeCode"))
        == "NO_PRESCRIPTION_REQUIRED",
    },
    "consumer_guidance": {
        "minimum_age": next(
            (
                text(n)
                for n in find_all(root, "targetConsumerMinimumUsage")
                if attr(n, "measurementUnitCode") == "ANN"
            ),
            None,
        )
    },
    "allergens": [
        {
            "type": text(find_first(a, "allergenTypeCode")),
            "containment": text(find_first(a, "levelOfContainmentCode")),
        }
        for a in find_all(root, "allergen")
    ],
    "ingredients": {
        "food": [
            {
                "lang": attr(n, "languageCode"),
                "text": text(n),
            }
            for n in find_all(root, "ingredientStatement")
        ],
        "non_food": [
            {
                "lang": attr(n, "languageCode"),
                "text": text(n),
            }
            for n in find_all(root, "nonfoodIngredientStatement")
        ],
    },
    "consumer_instructions": {
        "usage": [
            {"lang": attr(n, "languageCode"), "text": text(n)}
            for n in find_all(root, "consumerUsageInstructions")
        ],
        "storage": [
            {"lang": attr(n, "languageCode"), "text": text(n)}
            for n in find_all(root, "consumerStorageInstructions")
        ],
        "recycling": [
            {"lang": attr(n, "languageCode"), "text": text(n)}
            for n in find_all(root, "consumerRecyclingInstructions")
        ],
    },
    "marketing": {
        "long": [
            {"lang": attr(n, "languageCode"), "text": text(n)}
            for n in find_all(root, "tradeItemMarketingMessage")
        ],
        "short": [
            {"lang": attr(n, "languageCode"), "text": text(n)}
            for n in find_all(root, "shortTradeItemMarketingMessage")
        ],
        "keywords": [
            {"lang": attr(n, "languageCode"), "text": text(n)}
            for n in find_all(root, "tradeItemKeyWords")
        ],
    },
    "packaging": {
        "type": text(find_first(root, "packagingTypeCode")),
        "is_returnable": text(find_first(root, "isPackagingMarkedReturnable"))
        == "true",
        "deposit_id": text(find_first(root, "returnablePackageDepositIdentification")),
    },
    "safety": {
        "is_dangerous_substance": text(find_first(root, "isDangerousSubstance"))
        == "TRUE",
    },
    "sales_restrictions": {
        "condition_code": text(find_first(root, "consumerSalesConditionCode")),
        "restricted": bool(find_first(root, "consumerSalesConditionCode")),
    },
    "media": [
        {
            "type": text(find_first(f, "referencedFileTypeCode")),
            "uri": text(find_first(f, "uniformResourceIdentifier")),
            "primary": text(find_first(f, "isPrimaryFile")) == "TRUE",
        }
        for f in find_all(root, "referencedFileHeader")
    ],
}

with OUT_PATH.open("w", encoding="utf-8") as f:
    json.dump(compact, f, ensure_ascii=False, indent=2)

print("✅ cin_compact.json written")
