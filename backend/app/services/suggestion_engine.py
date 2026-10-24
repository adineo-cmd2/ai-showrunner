def suggest(story_state: dict) -> dict:
    story_state = story_state or {}
    guns = list(story_state.get("guns") or [])
    char_last_seen = dict(story_state.get("char_last_seen") or {})
    rules_refcounts = dict(story_state.get("rules_refcounts") or {})

    if guns:
        oldest = min(guns, key=lambda g: g.get("first_seen", 0))
        payoff = oldest.get("suggestion") or (
            f"Pay off '{oldest.get('entity')}' (introduced ep "
            f"{oldest.get('first_seen')}, unmentioned since)"
        )
    else:
        payoff = "No open setups — plant a new mystery."

    if char_last_seen:
        name = min(char_last_seen, key=lambda k: char_last_seen[k])
        beat = f"Bring back {name} (last seen ep {char_last_seen[name]})."
    else:
        beat = "Introduce a new voice."

    if rules_refcounts:
        rule = min(rules_refcounts, key=lambda k: rules_refcounts[k])
        world = f"Explore '{rule}' in the next episode."
    else:
        world = "No world rules yet — write one."

    return {"payoff": payoff, "beat": beat, "world": world}
