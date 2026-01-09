import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any

# =========================================================
# Namespaces
# =========================================================

NS = {
    "cin": "urn:gs1:gdsn:catalogue_item_notification:xsd:3",
    "allergen": "urn:gs1:gdsn:allergen_information:xsd:3",
    "ingredient": "urn:gs1:gdsn:food_and_beverage_ingredient:xsd:3",
    "nutrition": "urn:gs1:gdsn:nutritional_information:xsd:3",
    "diet": "urn:gs1:gdsn:diet_information:xsd:3",
    "battery": "urn:gs1:gdsn:battery_information:xsd:3",
    "danger": "urn:gs1:gdsn:dangerous_substance_information:xsd:3",
    "nonfood": "urn:gs1:gdsn:nonfood_ingredient:xsd:3",
    "healthcare": "urn:gs1:gdsn:healthcare_item_information:xsd:3",
    "material": "urn:gs1:gdsn:material:xsd:3",
    "ref": "urn:gs1:gdsn:referenced_file_detail_information:xsd:3",
    "prep": "urn:gs1:gdsn:food_and_beverage_preparation_serving:xsd:3",
    "safety": "urn:gs1:gdsn:safety_data_sheet:xsd:3",
    "sustain": "urn:gs1:gdsn:sustainability_module:xsd:3",
    "handling": "urn:gs1:gdsn:trade_item_handling:xsd:3",
}

# =========================================================
# Helpers
# =========================================================


def _text(root: ET.Element, path: str) -> Optional[str]:
    el = root.find(path, NS)
    if el is not None and el.text:
        return el.text.strip()
    return None


def _texts(root: ET.Element, path: str) -> List[str]:
    return [
        el.text.strip() for el in root.findall(path, NS) if el.text and el.text.strip()
    ]


# =========================================================
# Extraction
# =========================================================


def extract_cin_signals(cin_xml: str) -> Dict[str, Any]:
    root = ET.fromstring(cin_xml)
    sales_condition = _text(root, ".//consumerSalesConditionCode")

    signals: Dict[str, Any] = {
        # -------------------------------------------------
        # Identity & ownership
        # -------------------------------------------------
        "identity": {
            "gtin": _text(root, ".//gtin"),
            "brand": _text(root, ".//brandName"),
            "supplier_assigned_id": _text(
                root,
                ".//additionalTradeItemIdentification[@additionalTradeItemIdentificationTypeCode='SUPPLIER_ASSIGNED']",
            ),
            "trade_channel": _text(root, ".//tradeItemTradeChannelCode"),
            "information_provider": {
                "gln": _text(root, ".//informationProviderOfTradeItem/gln"),
                "name": _text(root, ".//informationProviderOfTradeItem/partyName"),
                "address": _text(
                    root, ".//informationProviderOfTradeItem/partyAddress"
                ),
            },
            "manufacturer": {
                "gln": _text(root, ".//manufacturerOfTradeItem/gln"),
                "name": _text(root, ".//manufacturerOfTradeItem/partyName"),
            },
        },
        # -------------------------------------------------
        # Classification
        # -------------------------------------------------
        "classification": {
            "gpc_code": _text(root, ".//gpcCategoryCode"),
            "gpc_name": _text(root, ".//gpcCategoryName"),
        },
        # -------------------------------------------------
        # Market & origin
        # -------------------------------------------------
        "market": {
            "target_country_code": _text(root, ".//targetMarketCountryCode"),
            "country_of_origin": _text(root, ".//countryOfOrigin/countryCode"),
        },
        # -------------------------------------------------
        # Naming & descriptions (multilingual safe)
        # -------------------------------------------------
        "naming": {
            "description_short": [
                {
                    "lang": d.attrib.get("languageCode"),
                    "text": d.text,
                }
                for d in root.findall(".//descriptionShort")
                if d.text
            ],
            "functional_name": [
                {
                    "lang": f.attrib.get("languageCode"),
                    "text": f.text,
                }
                for f in root.findall(".//functionalName")
                if f.text
            ],
            "regulated_product_name": [
                {
                    "lang": r.attrib.get("languageCode"),
                    "text": r.text,
                }
                for r in root.findall(".//regulatedProductName")
                if r.text
            ],
        },
        # -------------------------------------------------
        # VAT / tax
        # -------------------------------------------------
        "vat": {
            "rate": _text(root, ".//dutyFeeTaxRate"),
            "type": _text(root, ".//dutyFeeTaxTypeCode"),
        },
        # -------------------------------------------------
        # Trade unit flags
        # -------------------------------------------------
        "trade_unit": {
            "is_consumer_unit": _text(root, ".//isTradeItemAConsumerUnit"),
            "is_base_unit": _text(root, ".//isTradeItemABaseUnit"),
            "is_variable_unit": _text(root, ".//isTradeItemAVariableUnit"),
            "is_orderable_unit": _text(root, ".//isTradeItemAnOrderableUnit"),
            "is_invoice_unit": _text(root, ".//isTradeItemAnInvoiceUnit"),
        },
        # -------------------------------------------------
        # Size & measurements
        # -------------------------------------------------
        "size": {
            "descriptive": _text(root, ".//descriptiveSizeDimension"),
            "net_content": _text(root, ".//netContent"),
        },
        "measurements": {
            "width_mm": _text(root, ".//width"),
            "height_mm": _text(root, ".//height"),
            "depth_mm": _text(root, ".//depth"),
            "gross_weight_g": _text(root, ".//grossWeight"),
            "net_weight_g": _text(root, ".//netWeight"),
            "nesting": {
                "direction": _text(root, ".//nestingDirectionCode"),
                "increment": _text(root, ".//nestingIncrement"),
                "type": _text(root, ".//nestingTypeCode"),
            },
        },
        # -------------------------------------------------
        # Diet
        # -------------------------------------------------
        "diet": {
            "description_sv": _text(root, ".//dietTypeDescription[@languageCode='sv']"),
            "types": [
                {
                    "code": _text(d, ".//dietTypeCode"),
                    "marked_on_package": _text(d, ".//isDietTypeMarkedOnPackage"),
                }
                for d in root.findall(".//dietTypeInformation", NS)
            ],
        },
        # -------------------------------------------------
        # Allergens
        # -------------------------------------------------
        "allergens": {
            "specification_agency": _text(root, ".//allergenSpecificationAgency"),
            "specification_name": _text(root, ".//allergenSpecificationName"),
            "items": [
                {
                    "code": _text(a, ".//allergenTypeCode"),
                    "containment": _text(a, ".//levelOfContainmentCode"),
                }
                for a in root.findall(".//allergen:allergen", NS)
            ],
        },
        # -------------------------------------------------
        # Ingredients
        # -------------------------------------------------
        "ingredients": {
            "food_statement": _text(root, ".//ingredient:ingredientStatement"),
            "additives": [
                {
                    "name": _text(a, ".//additiveName"),
                    "containment": _text(a, ".//levelOfContainmentCode"),
                }
                for a in root.findall(".//additiveInformation")
            ],
        },
        # -------------------------------------------------
        # Preparation / serving
        # -------------------------------------------------
        "preparation": {
            "type_code": _text(root, ".//prep:preparationTypeCode"),
        },
        # -------------------------------------------------
        # Nutrition
        # -------------------------------------------------
        "nutrition": {
            "basis_quantity": _text(root, ".//nutrition:nutrientBasisQuantity"),
            "nutrients": [
                {
                    "type": _text(n, ".//nutrientTypeCode"),
                    "values": [
                        {
                            "value": qc.text,
                            "unit": qc.attrib.get("measurementUnitCode"),
                        }
                        for qc in n.findall(".//quantityContained")
                    ],
                }
                for n in root.findall(".//nutrition:nutrientDetail", NS)
            ],
        },
        # -------------------------------------------------
        # Packaging
        # -------------------------------------------------
        "packaging": {
            "type": _text(root, ".//packagingTypeCode"),
            "is_returnable": _text(root, ".//isPackagingMarkedReturnable"),
            "is_price_on_pack": _text(root, ".//isPriceOnPack"),
            "materials": [
                {
                    "material_type": _text(m, ".//packagingMaterialTypeCode"),
                    "weight": _text(m, ".//packagingMaterialCompositionQuantity"),
                }
                for m in root.findall(".//packagingMaterial")
            ],
        },
        # -------------------------------------------------
        # Handling & stacking
        # -------------------------------------------------
        "handling": {
            "instructions": _texts(root, ".//handlingInstructionsCodeReference"),
            "stacking": {
                "factor": _text(root, ".//stackingFactor"),
                "type": _text(root, ".//stackingFactorTypeCode"),
            },
        },
        # -------------------------------------------------
        # Media / images / files
        # -------------------------------------------------
        "media": [
            {
                "type": _text(f, ".//referencedFileTypeCode"),
                "format": _text(f, ".//fileFormatName"),
                "file_name": _text(f, ".//fileName"),
                "uri": _text(f, ".//uniformResourceIdentifier"),
                "is_primary": _text(f, ".//isPrimaryFile"),
                "width_px": _text(f, ".//filePixelWidth"),
                "height_px": _text(f, ".//filePixelHeight"),
                "size": _text(f, ".//fileSize"),
            }
            for f in root.findall(".//ref:referencedFileHeader", NS)
        ],
        # -------------------------------------------------
        # Sustainability
        # -------------------------------------------------
        "sustainability": {
            "contains_pesticide": _text(root, ".//doesTradeItemContainPesticide"),
        },
        # -------------------------------------------------
        # Safety
        # -------------------------------------------------
        "safety": {
            "regulated_for_transport": _text(root, ".//isRegulatedForTransportation"),
        },
        # -------------------------------------------------
        # Sales
        # -------------------------------------------------
        "sales": {
            "price_comparison_value": _text(root, ".//priceComparisonMeasurement"),
            "price_comparison_unit": _text(root, ".//priceComparisonContentTypeCode"),
        },
        # -------------------------------------------------
        # Dates
        # -------------------------------------------------
        "dates": {
            "start_availability": _text(root, ".//startAvailabilityDateTime"),
            "last_change": _text(root, ".//lastChangeDateTime"),
            "effective_date": _text(root, ".//effectiveDateTime"),
            "publication_date": _text(root, ".//publicationDateTime"),
        },
        # -------------------------------------------------
        # Sales restrictions
        # -------------------------------------------------
        "sales_restrictions": {
            "consumer_sale_restricted": sales_condition is not None,
            "condition_code": sales_condition,
        },
    }

    return signals
