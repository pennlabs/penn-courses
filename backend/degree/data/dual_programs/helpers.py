THIS_BLOCK = [{"kind": "THISBLOCK", "value": None}]


def q_course(full_code: str) -> str:
    return f"<Q: (AND: ('full_code', '{full_code}'))>"


def q_any(full_codes: list[str]) -> str:
    parts = ", ".join(f"('full_code', '{code}')" for code in full_codes)
    return f"<Q: (OR: {parts})>"


def q_attr(*codes: str) -> str:
    listed = ", ".join(f"'{code}'" for code in codes)
    return f"<Q: (AND: ('attributes__code__in', [{listed}]))>"


def q_department_range(department: str, low: str, high: str) -> str:
    return (
        f"<Q: (AND: ('department__code', '{department}'), "
        f"('code__gte', '{low}'), ('code__lte', '{high}'))>"
    )


def q_any_course() -> str:
    return "<Q: (AND: ('code__gte', '0000'))>"


def leaf(title, q, block_value, *, num=None, credits=None, share_targets=None):
    return {
        "title": title,
        "q": q,
        "num": num,
        "credits": credits,
        "share_targets": share_targets or [],
        "block_type": "VARIANT",
        "block_value": block_value,
        "children": [],
    }


def group(title, block_value, children, *, num=None):
    return {
        "title": title,
        "q": "",
        "num": num,
        "credits": None,
        "share_targets": [],
        "block_type": "VARIANT",
        "block_value": block_value,
        "children": children,
    }
