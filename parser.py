"""Parser helpers for aggregating and validating invoice JSON across pages.

All helpers operate on a common schema:
{
  "vendor_name": str,
  "invoice_number": str,
  "invoice_date": str,
  "due_date": str,
  "bill_to": str,
  "line_items": list[ {description, quantity, unit_price, total_price} ],
  "subtotal": str,
  "tax": str,
  "grand_total": str,
  "payment_info": str
}
"""

from typing import List, Dict, Any


def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge a list of per-page extraction dicts into a single invoice dict.

    Rules:
    - First non-empty value wins for scalar fields.
    - Line items are concatenated across pages.
    - Subtotals/tax/total prefer the last non-empty value (often on final page).
    """
    merged = {
        "vendor_name": "",
        "invoice_number": "",
        "invoice_date": "",
        "due_date": "",
        "bill_to": "",
        "line_items": [],
        "subtotal": "",
        "tax": "",
        "grand_total": "",
        "payment_info": "",
    }

    # First non-empty for headers
    header_keys_first = [
        "vendor_name",
        "invoice_number",
        "invoice_date",
        "due_date",
        "bill_to",
        "payment_info",
    ]

    # Last non-empty for totals
    footer_keys_last = ["subtotal", "tax", "grand_total"]

    for page in results:
        if not isinstance(page, dict):
            continue
        for key in header_keys_first:
            if not merged[key] and page.get(key):
                merged[key] = page[key]
        # Extend items
        items = page.get("line_items") or []
        if isinstance(items, list):
            merged["line_items"].extend(items)
        # Track totals as last non-empty
        for key in footer_keys_last:
            if page.get(key):
                merged[key] = page[key]

    return merged


def validate_invoice_json(data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure output follows the expected schema; coerce missing fields.

    Returns the same dict, corrected.
    """
    expected = {
        "vendor_name": "",
        "invoice_number": "",
        "invoice_date": "",
        "due_date": "",
        "bill_to": "",
        "line_items": [],
        "subtotal": "",
        "tax": "",
        "grand_total": "",
        "payment_info": "",
    }

    if not isinstance(data, dict):
        data = {}

    # Fill missing keys and coerce types
    for k, default in expected.items():
        if k not in data:
            data[k] = default
        else:
            if k == "line_items":
                if not isinstance(data[k], list):
                    data[k] = []
            else:
                if data[k] is None:
                    data[k] = default
                elif not isinstance(data[k], str):
                    data[k] = str(data[k])

    return data
