"""Unit, area and listings-index pages generated from data/listings.json.
The listings file is refreshed from the Listing Hub (Victor's own C&I listings + his starred ones), then build.py runs."""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))

def slugify(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")

def money(n):
    if n is None: return ""
    if n >= 1_000_000: return f"RM{n/1_000_000:.2f}".rstrip("0").rstrip(".") + "M"
    return f"RM{n:,.0f}"

def load():
    units = json.load(open(os.path.join(HERE, "data", "listings.json"), encoding="utf-8"))
    for u in units:
        deal = "for sale or rent" if u.get("sale") and u.get("rent") else ("for sale" if u.get("sale") else "for rent")
        u["deal"] = deal
        u["title"] = f'{u["category"]} {deal}, {u["area"]}'
        size = f'{u["builtup_sqft"]} sqft' if u.get("builtup_sqft") else (u.get("land_text") or "").replace("'","").replace("×","x")
        u["slug"] = slugify(f'{u["category"]} {deal} {u["area"]} {size}')
        u["area_slug"] = slugify(u["area"])
        parts = []
        if u.get("sale"): parts.append(money(u["sale"]))
        if u.get("rent"): parts.append(f'{money(u["rent"])}/mo')
        u["price_text"] = " · or ".join(parts) if len(parts) == 2 else (parts[0] if parts else "Price on request")
        specs = []
        if u.get("land_sqft"): specs.append(f'Land {u["land_sqft"]:,} sqft')
        elif u.get("land_text"): specs.append(f'Land {u["land_text"]}')
        if u.get("builtup_sqft"): specs.append(f'Built-up {u["builtup_sqft"]:,} sqft')
        for k in ("industry", "power", "tenure"):
            if u.get(k): specs.append(u[k])
        u["spec_line"] = " · ".join(specs)
        u["psf"] = round(u["rent"] / u["builtup_sqft"], 2) if u.get("rent") and u.get("builtup_sqft") else None
    units.sort(key=lambda u: u["listed"], reverse=True)
    return units
