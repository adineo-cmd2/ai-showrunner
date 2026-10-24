def find_guns(mentions: list, current_ep: int, active_titles=None) -> list:
    grouped: dict = {}
    for m in mentions or []:
        entity = m.get("entity")
        ep = m.get("episode")
        if not entity or ep is None:
            continue
        info = grouped.setdefault(entity, {"count": 0, "first_seen": ep, "last_seen": ep})
        info["count"] += 1
        info["first_seen"] = min(info["first_seen"], ep)
        info["last_seen"] = max(info["last_seen"], ep)

    guns = []
    if active_titles is not None:
        allowed = []
        norms = [(t or "").strip().lower() for t in active_titles]
        for entity, info in grouped.items():
            ent = (entity or "").strip().lower()
            if any(ent and (ent in title or title == ent) for title in norms):
                allowed.append(entity)
    else:
        allowed = list(grouped.keys())
    for entity in allowed:
        info = grouped[entity]
        if info["count"] == 1 and info["first_seen"] <= current_ep - 2:
            guns.append(
                {
                    "entity": entity,
                    "first_seen": info["first_seen"],
                    "last_seen": info["last_seen"],
                    "suggestion": (
                        f"Pay off '{entity}' (introduced ep {info['first_seen']}, "
                        "unmentioned since)"
                    ),
                }
            )
    guns.sort(key=lambda g: g["first_seen"])
    return guns
