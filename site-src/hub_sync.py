"""Sync data/listings.json with Victor's Listing Hub website feed (Google Drive: Website Photos/_feeds/Victor Tai.json).

    python3 site-src/hub_sync.py <feed.json> <photos dir>

<photos dir> holds the Hub photo folders (<photoFolder>/1.jpg ...) for the units that have photos.
- New commercial / industrial units in the feed are added (structured fields only, never the original message).
- Units no longer in the feed (sold, rented, withdrawn, unstarred) are removed.
- Units already on the site keep their hand-written text; only price and size are refreshed.
Prints one line per change. Exit code 0 when nothing changed, 10 when listings.json changed.
"""
import json, os, re, shutil, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data", "listings.json")
CI = {"Shop / Office": "com", "Factory / Warehouse": "ind", "Land": "ind"}


def num(v):
    if v is None: return None
    if isinstance(v, (int, float)): return int(v)
    s = re.sub(r"[^\d.]", "", str(v))
    return int(float(s)) if re.fullmatch(r"[\d,\s]+(sqft|sf)?", str(v).strip(), re.I) and s else None


def new_unit(f):
    title = f.get("title") or ""
    cat, _, estate = title.partition(",")
    cat = cat.strip() or f.get("category") or "Unit"
    estate = re.sub(r"\s*\(.*?\)\s*$", "", estate.strip()) or f.get("area") or ""
    deal = (f.get("deal") or "").lower()
    land_n = num(f.get("land"))
    u = {"id": f["id"], "hub_ids": [f["id"]], "kind": CI[f["category"]], "category": cat[:1].upper() + cat[1:],
         "area": f.get("area") or estate, "estate": estate,
         "sale": f.get("price") if "sale" in deal else None, "rent": f.get("rent") if "rent" in deal else None,
         "land_sqft": land_n, "builtup_sqft": num(f.get("builtup")),
         "power": f.get("power") or "", "industry": (f.get("industrial") or "").split("·")[0].strip(),
         "tenure": f.get("tenure") or "", "features": [f["furnish"]] if f.get("furnish") else [],
         "available": "", "photos": [],
         "listed": time.strftime("%Y-%m-%d", time.gmtime((f.get("updatedAt") or time.time() * 1000) / 1000 + 8 * 3600))}
    if not land_n and f.get("land"): u["land_text"] = f["land"]
    return u


def main(feed_path, photos_root):
    feed = [f for f in json.load(open(feed_path, encoding="utf-8")).get("units", [])
            if f.get("category") in CI and f.get("status", "Available") == "Available"]
    units = json.load(open(DATA, encoding="utf-8"))
    ids = {f["id"] for f in feed}
    changed = []
    # remove units no longer in the feed (only when the feed looks complete)
    if len(feed) >= 2:
        keep = []
        for u in units:
            if set(u.get("hub_ids") or [u["id"]]) & ids: keep.append(u)
            else: changed.append(f"removed {u['category']}, {u['area']}")
        units = keep
    have = {h for u in units for h in (u.get("hub_ids") or [u["id"]])}
    for f in feed:
        if f["id"] in have:
            u = next(x for x in units if f["id"] in (x.get("hub_ids") or [x["id"]]))
            deal = (f.get("deal") or "").lower()
            for k, v in (("sale", f.get("price") if "sale" in deal else u.get("sale")), ("rent", f.get("rent") if "rent" in deal else u.get("rent"))):
                if v and v != u.get(k): changed.append(f"{k} {u.get(k)} -> {v}: {u['category']}, {u['area']}"); u[k] = v
            continue
        u = new_unit(f)
        units.append(u); changed.append(f"added {u['category']}, {u['area']} ({u['id']})")
    # photos for every unit that has none yet
    for f in feed:
        src = os.path.join(photos_root, f.get("photoFolder") or "") if f.get("photoFolder") else None
        dst = os.path.join(HERE, "photos", f["id"])
        if src and os.path.isdir(src) and not os.path.isdir(dst):
            fs = sorted(x for x in os.listdir(src) if x.lower().endswith((".jpg", ".jpeg", ".png")))
            if fs:
                os.makedirs(dst); [shutil.copy(os.path.join(src, x), dst) for x in fs]
                changed.append(f"photos {len(fs)} for {f['id']}")
    if not changed: print("no change"); return 0
    with open(DATA, "w", encoding="utf-8") as o:
        o.write("[\n" + ",\n".join(" " + json.dumps(u, ensure_ascii=False, separators=(",", ":")) for u in units) + "\n]\n")
    print("\n".join(changed)); return 10


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
