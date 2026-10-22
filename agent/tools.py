"""LaptopAdvisor tools: a synthetic catalog of 30 laptops covering all budgets and use cases.

Each tool has a clear one-line docstring — the ToolSelector pattern uses it as the option
description when asking Strands Decider 2B which tool should handle the user's request.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from strands import tool

# ---------------------------------------------------------------------------
# Catalog loader
# ---------------------------------------------------------------------------

def _load_catalog() -> list[dict[str, Any]]:
    data_file = Path(__file__).parent / "data" / "laptops.json"
    with open(data_file, encoding="utf-8") as fh:
        return json.load(fh)

CATALOG: list[dict[str, Any]] = _load_catalog()


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def search_laptops(use_case: str, budget: float = 0) -> dict:
    """Search the laptop catalog by use case (e.g. gaming, student, developer) and optional maximum budget."""
    uc = use_case.lower().strip()
    # Map common synonyms
    synonyms = {
        "coding": "developer", "programming": "developer", "software": "developer",
        "work": "business", "office": "business", "corporate": "business",
        "college": "student", "school": "student", "university": "student",
        "video": "video-editing", "editing": "video-editing", "youtube": "video-editing",
        "machine learning": "data-science", "ml": "data-science", "ai": "data-science",
        "3d": "3d-rendering", "cad": "3d-rendering", "rendering": "3d-rendering",
        "cheap": "budget", "affordable": "budget", "low cost": "budget",
        "travel": "business",  # travellers usually want light business machines
    }
    for kw, mapped in synonyms.items():
        if kw in uc:
            uc = mapped
            break

    results = [
        lap for lap in CATALOG
        if any(uc in u for u in lap["use_cases"])
    ]
    if budget and budget > 0:
        results = [lap for lap in results if lap["price"] <= budget]

    if not results:
        # Fallback: return general laptops within budget
        results = [lap for lap in CATALOG if "general" in lap["use_cases"]]
        if budget and budget > 0:
            results = [lap for lap in results if lap["price"] <= budget]

    results = sorted(results, key=lambda l: -l["rating"])[:5]
    return {
        "use_case": use_case,
        "budget": budget if budget else "any",
        "count": len(results),
        "laptops": [
            {"model": f"{l['brand']} {l['model']}", "price": l["price"],
             "ram_gb": l["ram_gb"], "storage_gb": l["storage_gb"],
             "battery_hours": l["battery_hours"], "weight_kg": l["weight_kg"],
             "rating": l["rating"], "os": l["os"], "use_cases": l["use_cases"]}
            for l in results
        ],
    }


@tool
def compare_laptops(model_a: str, model_b: str) -> dict:
    """Compare two laptop models side by side on specs, price, battery, weight and ratings."""
    def _find(query: str) -> dict | None:
        q = query.lower().strip()
        for lap in CATALOG:
            full = f"{lap['brand']} {lap['model']}".lower()
            if q in full or full in q or lap["model"].lower() in q:
                return lap
        return None

    a, b = _find(model_a), _find(model_b)
    if not a:
        return {"error": f"Laptop not found: {model_a}. Try a brand + model name like 'MacBook Air 15 M3'."}
    if not b:
        return {"error": f"Laptop not found: {model_b}. Try a brand + model name like 'Dell XPS 13 Plus'."}

    def _row(lap: dict) -> dict:
        return {
            "model": f"{lap['brand']} {lap['model']}",
            "price_usd": lap["price"],
            "ram_gb": lap["ram_gb"],
            "storage_gb": lap["storage_gb"],
            "gpu": lap["gpu"],
            "display_inch": lap["display_inch"],
            "weight_kg": lap["weight_kg"],
            "battery_hours": lap["battery_hours"],
            "os": lap["os"],
            "use_cases": lap["use_cases"],
            "rating": lap["rating"],
        }

    cheaper = f"{a['brand']} {a['model']}" if a["price"] < b["price"] else f"{b['brand']} {b['model']}"
    longer_battery = f"{a['brand']} {a['model']}" if a["battery_hours"] >= b["battery_hours"] else f"{b['brand']} {b['model']}"
    lighter = f"{a['brand']} {a['model']}" if a["weight_kg"] <= b["weight_kg"] else f"{b['brand']} {b['model']}"

    return {
        "laptop_a": _row(a),
        "laptop_b": _row(b),
        "summary": {
            "cheaper": cheaper,
            "longer_battery": longer_battery,
            "lighter": lighter,
            "price_difference_usd": abs(a["price"] - b["price"]),
        },
    }


@tool
def filter_by_budget(max_price: float) -> dict:
    """List all laptops available within a given maximum price, sorted best-rated first."""
    results = [lap for lap in CATALOG if lap["price"] <= max_price]
    results = sorted(results, key=lambda l: -l["rating"])

    return {
        "max_price": max_price,
        "count": len(results),
        "laptops": [
            {"model": f"{l['brand']} {l['model']}", "price": l["price"],
             "ram_gb": l["ram_gb"], "battery_hours": l["battery_hours"],
             "rating": l["rating"], "os": l["os"], "use_cases": l["use_cases"]}
            for l in results[:8]
        ],
    }


@tool
def get_laptop_details(model: str) -> dict:
    """Get the full specifications and expert review summary for a specific laptop model."""
    query = model.lower().strip()
    found = None
    for lap in CATALOG:
        full = f"{lap['brand']} {lap['model']}".lower()
        if query in full or full in query or lap["model"].lower() in query:
            found = lap
            break

    if not found:
        return {"error": f"Laptop not found: {model}. Try a brand + model like 'MacBook Air 15 M3'."}

    return {
        "id": found["id"],
        "model": f"{found['brand']} {found['model']}",
        "price_usd": found["price"],
        "ram_gb": found["ram_gb"],
        "storage_gb": found["storage_gb"],
        "gpu": found["gpu"],
        "display_inch": found["display_inch"],
        "weight_kg": found["weight_kg"],
        "battery_hours": found["battery_hours"],
        "os": found["os"],
        "use_cases": found["use_cases"],
        "rating": found["rating"],
        "review": found["review"],
    }


TOOLS = [search_laptops, compare_laptops, filter_by_budget, get_laptop_details]
