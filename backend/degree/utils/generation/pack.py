"""
Lay suggestions into the student's semesters.

Pins (fulfillments that already have a semester) occupy credit first and are never moved,
including when that puts a semester over its cap. Ghosts only land in future, non-gap
semesters that still have room.
"""

from __future__ import annotations

import re

from courses.util import get_current_semester


DEFAULT_CU_CAP = 5.5
DEFAULT_SUMMER_CAP = 2.0
# How far past the last column we may add terms so a plan that ends at the current
# semester still receives the rest of the degree. Fall/spring only, so 8 is four years.
MAX_SYNTHETIC = 8
SEMESTER_KEY = re.compile(r"^\d{4}[ABC]$")
# SEAS senior design is a fixed senior-year placement, not a first-open-term filler.
# Fall of the fourth academic year, then spring. Same pairs as the degree planner.
SENIOR_DESIGN_SEASON = {
    "CIS-4000": "C",
    "CIS-4100": "C",
    "ESE-4500": "C",
    "MEAM-4450": "C",
    "BE-4950": "C",
    "MSE-4950": "C",
    "CBE-4000": "C",
    "CIS-4010": "A",
    "CIS-4110": "A",
    "ESE-4510": "A",
    "MEAM-4460": "A",
    "BE-4960": "A",
    "MSE-4960": "A",
    "CBE-4590": "A",
}


class PackError(ValueError):
    pass


def _validate(semesters):
    seen = set()
    cleaned = []
    for row in semesters:
        key = row.get("key")
        # AP/transfer lives under "_TRAN" and is not a term the schedule can fill.
        if not key or not SEMESTER_KEY.match(str(key)):
            continue
        if key in seen:
            raise PackError(f"Duplicate semester key: {key}")
        seen.add(key)
        cap = row.get("cu_cap")
        if cap is None:
            cap = DEFAULT_SUMMER_CAP if key.endswith("B") else DEFAULT_CU_CAP
        cap = float(cap)
        if cap <= 0:
            raise PackError(f"CU cap must be positive: {key}")
        cleaned.append({"key": key, "cu_cap": cap, "gap": bool(row.get("gap"))})
    if not cleaned:
        raise PackError("No semesters to schedule into.")
    cleaned.sort(key=lambda row: row["key"])
    return cleaned


def next_semester(key, allow_summer):
    year = int(key[:4])
    season = key[4]
    if season == "A":
        return f"{year}B" if allow_summer else f"{year}C"
    if season == "B":
        return f"{year}C"
    return f"{year + 1}A"


def _fillable(row, current, allow_summer):
    if row["key"] <= current:
        return False
    if row["gap"]:
        return False
    if row["key"].endswith("B") and not allow_summer:
        return False
    return True


def _academic_year(key):
    """Fall starts an academic year. The following spring and summer belong to it."""
    year = int(key[:4])
    if key.endswith("C"):
        return year
    return year - 1


def _anchor_year(rows, current):
    """Academic year of the earliest term on the plan. That year is year 1."""
    keys = [row["key"] for row in rows if not row["key"].endswith("B")]
    if not keys:
        keys = [current]
    return _academic_year(min(keys))


def _senior_code(item):
    code = item.get("full_code")
    if not code:
        label = (item.get("short_label") or item.get("label") or "").replace(" ", "-")
        code = label
    if code in SENIOR_DESIGN_SEASON:
        return code
    return None


def _senior_target(code, anchor):
    """Fourth academic year: fall is `anchor+3` C, spring is `anchor+4` A."""
    if SENIOR_DESIGN_SEASON[code] == "C":
        return f"{anchor + 3}C"
    return f"{anchor + 4}A"


def _sort_items(items):
    kind_order = {"placement": 0, "course": 1, "placeholder": 2}

    def key(item):
        return (
            kind_order.get(item["kind"], 9),
            item.get("course_number", 10**9),
            item["slot_ids"][0] if item["slot_ids"] else item.get("full_code") or "",
        )

    return sorted(items, key=key)


def pack(suggestions, semesters, allow_summer=False, pins=None, pinned_slots=None):
    rows = _validate(semesters)
    current = str(get_current_semester())
    used = {row["key"]: 0.0 for row in rows}
    for pin in pins or []:
        if pin["semester"] in used:
            used[pin["semester"]] += float(pin["cu"])

    placed = []
    unplaced = []
    synthetic = []
    pinned_semester = {
        pin.get("slot_id"): pin.get("semester")
        for pin in (pinned_slots or [])
        if pin.get("slot_id") and pin.get("semester")
    }

    def room(row):
        return row["cu_cap"] - used[row["key"]]

    def place_in(item, row):
        used[row["key"]] += float(item["cu"])
        placed.append({k: v for k, v in item.items() if k != "course_number"} | {"semester": row["key"]})

    def row_for(key):
        return next((row for row in rows if row["key"] == key), None)

    def extend_through(target):
        """Add future terms until `target` is on the grid, within the synthetic cap."""
        while rows and rows[-1]["key"] < target and len(synthetic) < MAX_SYNTHETIC:
            origin = rows[-1]["key"]
            nxt = next_semester(origin, allow_summer)
            if nxt in used:
                break
            cap = DEFAULT_SUMMER_CAP if nxt.endswith("B") else DEFAULT_CU_CAP
            row = {"key": nxt, "cu_cap": cap, "gap": False}
            if not _fillable(row, current, allow_summer):
                break
            synthetic.append(row)
            rows.append(row)
            used[nxt] = 0.0

    anchor = _anchor_year(rows, current)

    def place_senior(item, code):
        target = _senior_target(code, anchor)
        season = target[4]
        extend_through(target)
        preferred = row_for(target)
        if preferred and _fillable(preferred, current, allow_summer) and not preferred["gap"]:
            place_in(item, preferred)
            return True
        for row in rows:
            if row["key"] <= target or not row["key"].endswith(season):
                continue
            if _fillable(row, current, allow_summer):
                place_in(item, row)
                return True
        while len(synthetic) < MAX_SYNTHETIC:
            origin = rows[-1]["key"] if rows else current
            nxt = next_semester(origin, allow_summer)
            if nxt in used:
                break
            cap = DEFAULT_SUMMER_CAP if nxt.endswith("B") else DEFAULT_CU_CAP
            row = {"key": nxt, "cu_cap": cap, "gap": False}
            if not _fillable(row, current, allow_summer):
                break
            synthetic.append(row)
            rows.append(row)
            used[nxt] = 0.0
            if nxt.endswith(season) and nxt > target:
                place_in(item, row)
                return True
        return False

    for item in _sort_items(suggestions["items"]):
        slot_ids = item.get("slot_ids") or []
        pinned_key = next((pinned_semester[slot] for slot in slot_ids if slot in pinned_semester), None)
        if pinned_key:
            row = row_for(pinned_key)
            if row is not None:
                place_in(item, row)
                continue
        senior = _senior_code(item)
        if senior:
            if not place_senior(item, senior):
                unplaced.append(
                    {
                        "slot_id": item["slot_ids"][0] if item["slot_ids"] else None,
                        "full_code": item.get("full_code"),
                        "reason": "no_capacity",
                    }
                )
            continue
        landed = False
        for row in rows:
            if not _fillable(row, current, allow_summer):
                continue
            if room(row) + 1e-9 >= float(item["cu"]):
                place_in(item, row)
                landed = True
                break
        if landed:
            continue
        # Extend past the last known semester, at most twice. Summer is skipped unless allowed,
        # and a column that is still not in the future does not count as one of the two.
        origin = synthetic[-1]["key"] if synthetic else (rows[-1]["key"] if rows else current)
        while len(synthetic) < MAX_SYNTHETIC and not landed:
            origin = next_semester(origin, allow_summer)
            cap = DEFAULT_SUMMER_CAP if origin.endswith("B") else DEFAULT_CU_CAP
            row = {"key": origin, "cu_cap": cap, "gap": False}
            if not _fillable(row, current, allow_summer):
                continue
            if float(item["cu"]) > cap + 1e-9:
                break
            synthetic.append(row)
            rows.append(row)
            used[origin] = 0.0
            if room(row) + 1e-9 >= float(item["cu"]):
                place_in(item, row)
                landed = True
        if not landed:
            unplaced.append(
                {
                    "slot_id": item["slot_ids"][0] if item["slot_ids"] else None,
                    "full_code": item.get("full_code"),
                    "reason": "no_capacity",
                }
            )

    generated_cu = round(sum(item["cu"] for item in placed), 2)
    occupied = {item["semester"] for item in placed}
    return {
        "placements": placed,
        "semesters": [
            {"key": row["key"], "synthetic": True}
            for row in synthetic
            if row["key"] in occupied
        ],
        "unplaced": unplaced,
        "generated_cu": generated_cu,
    }
