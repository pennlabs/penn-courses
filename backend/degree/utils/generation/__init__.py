"""Stateless schedule generation: open slots, suggestions, then packing."""

from degree.utils.generation.pack import pack as pack_semesters
from degree.utils.generation.suggest import suggest as suggest_courses


def generate_schedule(
    degree_plan,
    semesters,
    allow_summer=False,
    pinned_slots=None,
    semester_overrides=None,
):
    """
    Propose a schedule for `degree_plan`.

    `semesters` is a list of `{key, cu_cap, gap}`. Existing fulfillments are pins and are
    never moved. `semester_overrides` is the grid the student is looking at, so a course
    they just dragged counts against that semester before the save lands. `pinned_slots`
    holds a requirement they dragged. Everything else is packed into the room that is left.
    The return value is a proposal; nothing is written.
    """
    suggestions = suggest_courses(degree_plan)
    overrides = semester_overrides or {}
    for pin in suggestions["pins"]:
        moved = overrides.get(pin.get("full_code"))
        if moved:
            pin["semester"] = moved
    packed = pack_semesters(
        suggestions,
        semesters,
        allow_summer=allow_summer,
        pins=suggestions["pins"],
        pinned_slots=pinned_slots,
    )
    return {
        "placements": packed["placements"],
        "semesters": packed["semesters"],
        "unplaced": packed["unplaced"],
        "open_rule_count": suggestions["open_rule_count"],
        "generated_cu": packed["generated_cu"],
    }
