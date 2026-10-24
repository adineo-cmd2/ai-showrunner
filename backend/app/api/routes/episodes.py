from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.routes.stories import _own_story
from app.db.session import get_db
from app.models.bible_change import BibleChange
from app.models.character import Character
from app.models.consistency_issue import ConsistencyIssue
from app.models.episode import Episode
from app.models.location import Location
from app.models.plot_thread import PlotThread
from app.models.user import User
from app.schemas.story import EpisodeCheckIn, EpisodeIn
from app.services import consistency_checker, entity_extractor
from app.services.episode_pipeline import analyse_episode

router = APIRouter()

_SEV_RANK = {"CRITICAL": 0, "WARNING": 1, "MINOR": 2}


def _bible_for_check(db: Session, story) -> tuple[dict, list]:
    story_id = story.id
    existing_chars = db.query(Character).filter(Character.story_id == story_id).all()
    existing_locs = db.query(Location).filter(Location.story_id == story_id).all()
    rules = list(getattr(story, "setting_rules", None) or [])
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
    seen = set()
    deaths = []
    for n in confirmed_deaths + pending_death_names:
        if n not in seen:
            seen.add(n)
            deaths.append(n)
    facts = []
    for c in existing_chars:
        ftext = " ".join(
            p for p in [c.name, c.traits or "", c.backstory or "", c.status or ""] if p
        ).strip()
        if ftext:
            facts.append({"subject": c.name, "text": ftext})
    for loc in existing_locs:
        ftext = " ".join(p for p in [loc.name, loc.description or ""] if p).strip()
        if ftext:
            facts.append({"subject": loc.name, "text": ftext})
    return {"deaths": deaths, "rules": rules, "facts": facts}, rules


@router.post("/{story_id}/episode")
def submit_episode(
    story_id: int,
    body: EpisodeIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    story = _own_story(db, user.id, story_id)
    result = analyse_episode(db, story, body.number, body.title or "", body.text or "")
    return {
        "episode_id": result["episode_id"],
        "issues": result["issues"],
        "pending": result["pending"],
        "guns": result["guns"],
    }


@router.post("/{story_id}/episode/check")
def check_episode(
    story_id: int,
    body: EpisodeCheckIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    story = _own_story(db, user.id, story_id)
    bible, rules = _bible_for_check(db, story)
    text = body.text or ""
    issues = consistency_checker.check(text, 0, bible)
    extracted = entity_extractor.extract(text, rules=rules)
    return {"issues": issues, "rule_hits": extracted.get("rule_hits", [])}


@router.get("/{story_id}/continuity")
def continuity(
    story_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    story = _own_story(db, user.id, story_id)
    rows = (
        db.query(ConsistencyIssue)
        .filter(ConsistencyIssue.story_id == story.id)
        .all()
    )
    ep_numbers = {
        e.id: e.number for e in db.query(Episode).filter(Episode.story_id == story.id).all()
    }
    rows.sort(key=lambda r: (_SEV_RANK.get(r.severity, 99), r.id))
    return {
        "issues": [
            {
                "id": r.id,
                "severity": r.severity,
                "kind": r.kind,
                "detail": r.detail,
                "passage": r.passage,
                "episode_id": r.episode_id,
                "episode_no": ep_numbers.get(r.episode_id, 0),
            }
            for r in rows
        ]
    }


def _thread_dict(t: PlotThread) -> dict:
    return {"id": t.id, "title": t.title, "status": t.status, "last_seen": t.last_seen}


@router.get("/{story_id}/threads")
def story_threads(
    story_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    story = _own_story(db, user.id, story_id)
    threads = (
        db.query(PlotThread)
        .filter(PlotThread.story_id == story.id)
        .order_by(PlotThread.id)
        .all()
    )
    episodes = db.query(Episode).filter(Episode.story_id == story.id).all()
    max_ep = max((e.number for e in episodes), default=0)
    active: list = []
    dormant: list = []
    resolved: list = []
    for t in threads:
        status = t.status or "active"
        if status == "resolved":
            resolved.append(_thread_dict(t))
        elif status == "dormant":
            dormant.append(_thread_dict(t))
        elif max_ep > 0 and (t.last_seen or 0) < max_ep - 1:
            dormant.append(_thread_dict(t))
        else:
            active.append(_thread_dict(t))
    return {"active": active, "dormant": dormant, "resolved": resolved}
