import re

from sqlalchemy.orm import Session

from app.models.bible_change import BibleChange
from app.models.character import Character
from app.models.consistency_issue import ConsistencyIssue
from app.models.episode import Episode
from app.models.location import Location
from app.models.plot_thread import PlotThread
from app.services import consistency_checker, entity_extractor, payoff_detector

_TOKEN_RE = re.compile(r"[a-z]{2,}")


def _get_story_id(story) -> int:
    if isinstance(story, int):
        return story
    return story.id


def _tokens(text: str) -> set:
    return set(_TOKEN_RE.findall((text or "").lower()))


def _thread_matches(title: str, entity: str) -> bool:
    low_title = (title or "").lower()
    low_ent = (entity or "").lower()
    if not low_ent:
        return False
    if low_ent in low_title or low_title in low_ent:
        return True
    return bool(_tokens(low_title) & _tokens(low_ent))


def _unique_keep_order(seq: list) -> list:
    seen = set()
    out = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def analyse_episode(db: Session, story, number: int, title: str, text: str) -> dict:
    story_id = _get_story_id(story)
    # Resolve story row for rules (story may be ORM or id)
    if isinstance(story, int):
        from app.models.story import Story

        story_row = db.query(Story).filter(Story.id == story).one()
    else:
        story_row = story

    ep = Episode(story_id=story_id, number=number, title=title or "", text=text or "")
    db.add(ep)
    db.commit()
    db.refresh(ep)

    existing_chars = db.query(Character).filter(Character.story_id == story_id).all()
    existing_locs = db.query(Location).filter(Location.story_id == story_id).all()
    known_names = [c.name for c in existing_chars]
    known_locations = [loc.name for loc in existing_locs]

    rules = list(getattr(story_row, "setting_rules", None) or [])

    extracted = entity_extractor.extract(
        text or "",
        known_names=known_names,
        rules=rules,
        known_locations=known_locations,
    )
    current_deaths = list(extracted.get("deaths", []))

    # Pending-gate: check against deaths recorded in PRIOR episodes only
    # (confirmed Characters + pending confirm_dead rows). Current-episode
    # deaths are emitted as pending below but excluded here, so a death
    # sentence never self-flags DEAD_ALIVE on its own episode. NEVER
    # mutate Character here.
    confirmed_deaths = [c.name for c in existing_chars if (c.status or "") == "dead"]
    pending_changes = (
        db.query(BibleChange)
        .filter(
            BibleChange.story_id == story_id,
            BibleChange.action == "confirm_dead",
            BibleChange.status == "pending",
        )
        .all()
    )
    pending_death_names = [
        (ch.payload or {}).get("name")
        for ch in pending_changes
        if isinstance(ch.payload, dict) and (ch.payload or {}).get("name")
    ]
    deaths_for_check = _unique_keep_order(confirmed_deaths + pending_death_names)

    facts = []
    for c in existing_chars:
        ftext = " ".join(
            p for p in [c.name, c.traits or "", c.backstory or "", c.status or ""] if p
        ).strip()
        if ftext:
            facts.append({"subject": c.name, "text": ftext})
    for loc in existing_locs:
        ftext = " ".join(
            p for p in [loc.name, loc.description or ""] if p
        ).strip()
        if ftext:
            facts.append({"subject": loc.name, "text": ftext})

    bible = {"deaths": deaths_for_check, "rules": rules, "facts": facts}
    found = consistency_checker.check(text or "", number, bible)

    issue_rows = []
    for iss in found:
        row = ConsistencyIssue(
            story_id=story_id,
            episode_id=ep.id,
            severity=iss["severity"],
            kind=iss["kind"],
            detail=iss["detail"],
            passage=iss["passage"],
        )
        db.add(row)
        issue_rows.append(row)
    db.commit()
    for row in issue_rows:
        db.refresh(row)

    # Death cues → ONLY pending BibleChange rows (PATCH confirm materialises).
    pending_rows = []
    known_pending_deaths = set(pending_death_names)
    for dead_name in _unique_keep_order(current_deaths):
        if dead_name in known_pending_deaths:
            continue
        known_pending_deaths.add(dead_name)
        change = BibleChange(
            story_id=story_id,
            episode_id=ep.id,
            action="confirm_dead",
            payload={"name": dead_name},
            status="pending",
        )
        db.add(change)
        pending_rows.append(change)
    if pending_rows:
        db.commit()
        for row in pending_rows:
            db.refresh(row)

    # New-name shells (alive + confirmed) — death names excluded (pending only).
    char_by_name = {c.name: c for c in existing_chars}
    loc_by_name = {loc.name: loc for loc in existing_locs}
    dead_set = set(current_deaths)
    loc_set = set(extracted.get("locations", []))
    existing_threads = (
        db.query(PlotThread).filter(PlotThread.story_id == story_id).all()
    )
    thread_titles = {t.title for t in existing_threads}

    def _ensure_thread(entity: str):
        if entity in thread_titles:
            return
        thread = PlotThread(
            story_id=story_id, title=entity, status="active", last_seen=number
        )
        db.add(thread)
        db.commit()
        db.refresh(thread)
        thread_titles.add(entity)

    shell_changes = []
    for name in extracted.get("names", []):
        if name in dead_set or name in char_by_name or name in loc_set:
            continue
        if name in loc_by_name:
            continue
        shell = Character(
            story_id=story_id,
            name=name,
            traits="",
            backstory="",
            status="alive",
            arc="",
        )
        db.add(shell)
        db.commit()
        db.refresh(shell)
        char_by_name[name] = shell
        _ensure_thread(name)
        change = BibleChange(
            story_id=story_id,
            episode_id=ep.id,
            action="add_character",
            payload={"name": name},
            status="confirmed",
        )
        db.add(change)
        shell_changes.append(change)

    # New-location shells + threads + confirmed changes.
    for loc_name in extracted.get("locations", []):
        if loc_name in loc_by_name:
            continue
        shell = Location(story_id=story_id, name=loc_name, description="")
        db.add(shell)
        db.commit()
        db.refresh(shell)
        loc_by_name[loc_name] = shell
        _ensure_thread(loc_name)
        change = BibleChange(
            story_id=story_id,
            episode_id=ep.id,
            action="add_location",
            payload={"name": loc_name},
            status="confirmed",
        )
        db.add(change)
        shell_changes.append(change)

    if shell_changes:
        db.commit()
        for row in shell_changes:
            db.refresh(row)
    pending_rows.extend(shell_changes)

    # Update thread last_seen for mentioned entities (both directions +
    # token overlap so custom titles like "Mara's debt" still match "Mara").
    mentioned = set(extracted.get("names", []))
    mentioned |= set(extracted.get("speakers", []))
    mentioned |= set(extracted.get("locations", []))
    threads = db.query(PlotThread).filter(PlotThread.story_id == story_id).all()
    for thread in threads:
        for entity in mentioned:
            if entity and _thread_matches(thread.title, entity):
                thread.last_seen = number
                break
    db.commit()

    # Guns: rebuild mentions from all episodes, filtered to active threads.
    all_eps = (
        db.query(Episode)
        .filter(Episode.story_id == story_id)
        .order_by(Episode.number)
        .all()
    )
    mentions = []
    for e in all_eps:
        ex = entity_extractor.extract(e.text or "")
        for n in ex.get("names", []):
            mentions.append({"entity": n, "episode": e.number})
    active_titles = [t.title for t in threads if (t.status or "") == "active"]
    guns = payoff_detector.find_guns(mentions, number, active_titles)

    issues_out = [
        {
            "severity": r.severity,
            "kind": r.kind,
            "detail": r.detail,
            "passage": r.passage,
        }
        for r in issue_rows
    ]
    pending_out = [
        {"id": r.id, "action": r.action, "payload": r.payload, "status": r.status}
        for r in pending_rows
    ]

    return {
        "episode_id": ep.id,
        "issues": issues_out,
        "pending": pending_out,
        "guns": guns,
        "rule_hits": extracted.get("rule_hits", []),
    }
